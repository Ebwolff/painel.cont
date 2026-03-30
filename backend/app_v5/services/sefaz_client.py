"""
SefazClient — Integração real com webservice nfeDistDFeInteresse da SEFAZ.
Autentica via certificado A1 (PFX) e retorna XMLs de NF-e para processamento.
Segurança: mTLS em memória (requests_pkcs12), TLS 1.2 mínimo.
"""
import logging
import requests
from typing import Optional
from requests_pkcs12 import post as pkcs12_post
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption
)
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from lxml import etree

logger = logging.getLogger(__name__)



# Endpoints por ambiente
SEFAZ_ENDPOINTS = {
    "producao": "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
    "homologacao": "https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx",
}

SOAP_ACTION = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe/nfeDistDFeInteresse"

NFE_NS = "http://www.portalfiscal.inf.br/nfe"
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"


class SefazClient:
    def __init__(self, ambiente: str = "homologacao"):
        self.ambiente = ambiente
        self.endpoint = SEFAZ_ENDPOINTS.get(ambiente, SEFAZ_ENDPOINTS["homologacao"])
        self.timeout = 30

    def extract_pem_from_pfx(self, pfx_bytes: bytes, password: str) -> tuple[str, str]:
        """
        Extrai cert PEM e key PEM de um arquivo PFX/P12 em memória.
        Retorna (cert_pem, key_pem) como strings.
        Lança ValueError se a senha estiver errada ou o arquivo inválido.
        """
        try:
            pw_bytes = password.encode("utf-8") if isinstance(password, str) else password
            private_key, certificate, _ = load_key_and_certificates(pfx_bytes, pw_bytes)

            cert_pem = certificate.public_bytes(Encoding.PEM).decode("utf-8")
            key_pem = private_key.private_bytes(
                Encoding.PEM, PrivateFormat.TraditionalOpenSSL, NoEncryption()
            ).decode("utf-8")
            return cert_pem, key_pem
        except Exception as e:
            raise ValueError(f"Certificado inválido ou senha incorreta: {e}")

    def build_soap_envelope(self, cnpj: str, ultimo_nsu: str = "000000000000000", codigo_uf: str = "35") -> str:
        """
        Monta o envelope SOAP 1.2 para nfeDistDFeInteresse.
        ultimo_nsu: NSU de referência, a SEFAZ retornará documentos com NSU maior.
        codigo_uf: Código IBGE do estado do autor (ex: 35=SP, 33=RJ, 31=MG).
        """
        # Remove formatação do CNPJ
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")

        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <nfeDistDFeInteresse xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeDistribuicaoDFe">
      <nfeDadosMsg>
        <distDFeInt versao="1.01" xmlns="{NFE_NS}">
          <tpAmb>{'1' if self.ambiente == 'producao' else '2'}</tpAmb>
          <cUFAutor>{codigo_uf}</cUFAutor>
          <CNPJ>{cnpj_limpo}</CNPJ>
          <distNSU>
            <ultNSU>{ultimo_nsu.zfill(15)}</ultNSU>
          </distNSU>
        </distDFeInt>
      </nfeDadosMsg>
    </nfeDistDFeInteresse>
  </soap12:Body>
</soap12:Envelope>"""
        return envelope

    def call_sefaz(
        self,
        pfx_bytes: bytes,
        password: str,
        cnpj: str,
        ultimo_nsu: str = "000000000000000",
        codigo_uf: str = "35",
    ) -> list[dict]:
        """
        Chama o webservice SEFAZ com autenticação mTLS e retorna lista de documentos.
        Cada documento: {"chave_acesso": str, "xml_content": bytes, "nsu": str, "tipo": str}
        """
        soap_body = self.build_soap_envelope(cnpj, ultimo_nsu, codigo_uf)

        headers = {
            "Content-Type": f'application/soap+xml; charset=utf-8; action="{SOAP_ACTION}"',
        }

        try:
            logger.info(f"SEFAZ: Conectando em {self.endpoint} para CNPJ {cnpj[:8]}***")
            # mTLS em memória — zero arquivos temporários
            response = pkcs12_post(
                self.endpoint,
                data=soap_body.encode("utf-8"),
                headers=headers,
                pkcs12_data=pfx_bytes,
                pkcs12_password=password,
                verify=True,
                timeout=self.timeout,
            )
            response.raise_for_status()
            logger.info(f"SEFAZ: Resposta recebida — HTTP {response.status_code}")
            return self._parse_response(response.content)

        except requests.exceptions.SSLError as e:
            logger.error(f"SEFAZ: Erro de SSL (certificado rejeitado?): {e}")
            raise RuntimeError(f"Certificado rejeitado pela SEFAZ: {e}")
        except requests.exceptions.Timeout:
            logger.error("SEFAZ: Timeout na requisição")
            raise RuntimeError("SEFAZ não respondeu dentro do tempo limite.")
        except requests.exceptions.HTTPError as e:
            err_msg = e.response.content.decode("utf-8", errors="replace") if e.response is not None else str(e)
            logger.error(f"SEFAZ: Erro HTTP {e.response.status_code if e.response else 'Unknown'}: {err_msg}")
            raise RuntimeError(f"Erro SEFAZ HTTP {e.response.status_code if e.response else 'Unknown'}: {err_msg[:500]}")
        except requests.exceptions.RequestException as e:
            logger.error(f"SEFAZ: Erro de conexão: {e}")
            raise RuntimeError(f"Erro de conexão com a SEFAZ: {e}")

    def _parse_response(self, xml_bytes: bytes) -> list[dict]:
        """
        Parseia a resposta SOAP da SEFAZ.
        Retorna lista de dicts com os XMls de NF-e/CT-e.
        """
        documentos = []
        try:
            root = etree.fromstring(xml_bytes)
            ns = {"nfe": NFE_NS, "soap": SOAP_NS}

            # Verifica cStat na resposta
            cstat_el = root.find(".//nfe:cStat", ns)
            cstat = cstat_el.text if cstat_el is not None else "?"
            xmot_el = root.find(".//nfe:xMotivo", ns)
            xmot = xmot_el.text if xmot_el is not None else ""

            logger.info(f"SEFAZ cStat={cstat} xMotivo={xmot}")

            # 138 = Documento(s) localizado(s) | 137 = Nenhum documento (NSU atual)
            if cstat == "656":
                logger.warning(f"SEFAZ 656: Consumo Indevido — {xmot}")
                raise RuntimeError(f"SEFAZ 656: {xmot}")

            if cstat not in ("138", "137", "000"):
                logger.warning(f"SEFAZ retornou status inesperado: {cstat} — {xmot}")
                return []

            # Itera sobre documentos retornados
            for doc_el in root.findall(".//nfe:docZip", ns):
                nsu = doc_el.get("NSU", "")
                schema = doc_el.get("schema", "")
                content_b64 = (doc_el.text or "").strip()

                if not content_b64:
                    continue

                import base64
                import gzip
                try:
                    xml_bytes_doc = gzip.decompress(base64.b64decode(content_b64))
                except Exception:
                    xml_bytes_doc = base64.b64decode(content_b64)

                # Tipo: resNFe (resumo) ou procNFe (completo)
                tipo = "nfe" if "nfe" in schema.lower() else "cte" if "cte" in schema.lower() else "outros"

                # Extrai chave de acesso do XML
                chave = self._extract_chave(xml_bytes_doc)

                documentos.append({
                    "nsu": nsu,
                    "chave_acesso": chave,
                    "xml_content": xml_bytes_doc,
                    "tipo": tipo,
                    "schema": schema,
                })

            logger.info(f"SEFAZ: {len(documentos)} documento(s) recebido(s)")

        except etree.XMLSyntaxError as e:
            logger.error(f"SEFAZ: Erro ao parsear resposta XML: {e}")

        return documentos

    def _extract_chave(self, xml_bytes: bytes) -> Optional[str]:
        """Extrai chNFe ou Id do XML da nota."""
        try:
            root = etree.fromstring(xml_bytes)
            ns = {"nfe": NFE_NS}
            # Tenta chNFe direto
            chave_el = root.find(".//nfe:chNFe", ns)
            if chave_el is not None:
                return chave_el.text
            # Tenta Id="NFe{chave}"
            for el in root.iter():
                id_attr = el.get("Id", "")
                if id_attr.startswith("NFe") and len(id_attr) == 47:
                    return id_attr[3:]
        except Exception:
            pass
        return None

    # ═══════════════════════════════════════════════
    # Manifestação do Destinatário (evento 210210)
    # ═══════════════════════════════════════════════

    SOAP_ACTION_EVENTO = (
        "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"
    )

    DESCRICOES_EVENTO = {
        "210200": "Confirmacao da Operacao",
        "210210": "Ciencia da Operacao",
        "210220": "Desconhecimento da Operacao",
        "210240": "Operacao nao Realizada",
    }

    def manifest_document(
        self,
        pfx_bytes: bytes,
        password: str,
        cnpj: str,
        chave_nfe: str,
        uf_empresa: str,
        n_seq_evento: int = 1,
        tp_evento: str = "210210",
    ) -> dict:
        """
        Envia evento de Manifestação do Destinatário para uma NF-e.

        Args:
            pfx_bytes: Conteúdo binário do PFX
            password: Senha do certificado
            cnpj: CNPJ da empresa destinatária
            chave_nfe: Chave de acesso da NF-e (44 dígitos)
            uf_empresa: Sigla da UF da empresa (ex: "SP")
            n_seq_evento: Sequência do evento (1 para primeira vez)
            tp_evento: Tipo do evento (default: 210210 Ciência)

        Returns:
            {"sucesso": bool, "protocolo": str|None, "cStat": str, "xMotivo": str}
        """
        from datetime import datetime, timezone
        from app_v5.services.xml_signer import XMLSigner
        from app_v5.services.sefaz_endpoints import (
            get_recepcao_evento_url, get_codigo_ibge_uf, gerar_id_lote,
        )

        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
        tp_amb = "1" if self.ambiente == "producao" else "2"

        # cOrgao: 91 = AN (obrigatório para manifestação do destinatário)
        c_orgao = "91"

        # ID: ID + tpEvento(6) + chNFe(44) + nSeqEvento(02) = 52 chars
        event_id = f"ID{tp_evento}{chave_nfe}{str(n_seq_evento).zfill(2)}"

        dh_evento = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S-03:00")
        x_evento = self.DESCRICOES_EVENTO.get(tp_evento, "Ciencia da Operacao")

        # 1. Montar XML do evento
        evento = etree.Element("evento", versao="1.00", xmlns=NFE_NS)
        inf = etree.SubElement(evento, "infEvento", Id=event_id)

        etree.SubElement(inf, "cOrgao").text = c_orgao
        etree.SubElement(inf, "tpAmb").text = tp_amb
        etree.SubElement(inf, "CNPJ").text = cnpj_limpo
        etree.SubElement(inf, "chNFe").text = chave_nfe
        etree.SubElement(inf, "dhEvento").text = dh_evento
        etree.SubElement(inf, "tpEvento").text = tp_evento
        etree.SubElement(inf, "nSeqEvento").text = str(n_seq_evento)
        etree.SubElement(inf, "verEvento").text = "1.00"

        det = etree.SubElement(inf, "detEvento", versao="1.00")
        etree.SubElement(det, "descEvento").text = x_evento

        # 2. Assinar XML com certificado A1
        signer = XMLSigner(pfx_bytes, password)
        evento_assinado = signer.sign_event(evento, event_id)

        # 3. Envelope envEvento
        env = etree.Element("envEvento", versao="1.00", xmlns=NFE_NS)
        etree.SubElement(env, "idLote").text = gerar_id_lote()
        env.append(evento_assinado)

        xml_str = etree.tostring(env, xml_declaration=False, encoding="unicode")

        # 4. SOAP 1.2 Envelope
        endpoint = get_recepcao_evento_url(uf_empresa, self.ambiente)

        soap = f'''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <nfeRecepcaoEvento xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4">
      <nfeDadosMsg>{xml_str}</nfeDadosMsg>
    </nfeRecepcaoEvento>
  </soap12:Body>
</soap12:Envelope>'''

        headers = {
            "Content-Type": f'application/soap+xml; charset=utf-8; action="{self.SOAP_ACTION_EVENTO}"',
        }

        # 5. Enviar com mTLS em memória
        logger.info(f"SEFAZ EVENTO: Enviando {tp_evento} para chave {chave_nfe[:20]}... (endpoint={endpoint})")

        try:
            response = pkcs12_post(
                endpoint,
                data=soap.encode("utf-8"),
                headers=headers,
                pkcs12_data=pfx_bytes,
                pkcs12_password=password,
                verify=False,  # SEFAZ estaduais usam CAs ICP-Brasil fora do trust store padrão
                timeout=self.timeout,
            )
            response.raise_for_status()
            return self._parse_evento_response(response.content)

        except requests.exceptions.SSLError as e:
            logger.error(f"SEFAZ EVENTO: Erro SSL: {e}")
            return {"sucesso": False, "cStat": "SSL", "xMotivo": str(e), "protocolo": None}
        except requests.exceptions.Timeout:
            logger.error("SEFAZ EVENTO: Timeout")
            return {"sucesso": False, "cStat": "TIMEOUT", "xMotivo": "Timeout", "protocolo": None}
        except requests.exceptions.RequestException as e:
            logger.error(f"SEFAZ EVENTO: Erro de conexão: {e}")
            return {"sucesso": False, "cStat": "CONN", "xMotivo": str(e), "protocolo": None}

    def _parse_evento_response(self, xml_bytes: bytes) -> dict:
        """Parseia resposta do RecepcaoEvento4."""
        try:
            root = etree.fromstring(xml_bytes)

            # Busca no retorno do evento (pode estar em diferentes levels)
            cstat_el = root.xpath("//*[local-name()='cStat']")
            xmot_el = root.xpath("//*[local-name()='xMotivo']")
            nprot_el = root.xpath("//*[local-name()='nProt']")

            # Pegar o cStat do retEvento (não do cabeçalho)
            # O primeiro cStat é do lote, o segundo é do evento individual
            cstat = cstat_el[-1].text if cstat_el else "?"
            xmotivo = xmot_el[-1].text if xmot_el else ""
            protocolo = nprot_el[0].text if nprot_el else None

            sucesso = cstat in ("135", "136")  # 135=Registrado, 136=Já Vinculado

            logger.info(f"SEFAZ EVENTO: cStat={cstat} xMotivo={xmotivo} nProt={protocolo}")

            return {
                "sucesso": sucesso,
                "cStat": cstat,
                "xMotivo": xmotivo,
                "protocolo": protocolo,
            }
        except etree.XMLSyntaxError as e:
            logger.error(f"SEFAZ EVENTO: Erro ao parsear resposta: {e}")
            return {"sucesso": False, "cStat": "PARSE", "xMotivo": str(e), "protocolo": None}

