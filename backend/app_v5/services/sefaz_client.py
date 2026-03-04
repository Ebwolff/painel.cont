"""
SefazClient — Integração real com webservice nfeDistDFeInteresse da SEFAZ.
Autentica via certificado A1 (PFX) e retorna XMLs de NF-e para processamento.
"""
import os
import tempfile
import logging
import requests
from typing import Optional
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

    def build_soap_envelope(self, cnpj: str, ultimo_nsu: str = "000000000000000") -> str:
        """
        Monta o envelope SOAP para nfeDistDFeInteresse.
        ultimo_nsu: NSU de referência, a SEFAZ retornará documentos com NSU maior.
        """
        # Remove formatação do CNPJ
        cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")

        # cUF 35 = São Paulo (padrão; a SEFAZ distribui para todos os estados)
        codigo_uf = os.getenv("SEFAZ_UF", "35")

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
        ultimo_nsu: str = "000000000000000"
    ) -> list[dict]:
        """
        Chama o webservice SEFAZ com autenticação mTLS e retorna lista de documentos.
        Cada documento: {"chave_acesso": str, "xml_content": bytes, "nsu": str, "tipo": str}
        """
        cert_pem, key_pem = self.extract_pem_from_pfx(pfx_bytes, password)
        soap_body = self.build_soap_envelope(cnpj, ultimo_nsu)

        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPAction": SOAP_ACTION,
        }

        # requests exige arquivos físicos para client cert — usamos tmpfiles em memória
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w") as cert_file:
            cert_file.write(cert_pem)
            cert_path = cert_file.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".key", mode="w") as key_file:
            key_file.write(key_pem)
            key_path = key_file.name

        try:
            logger.info(f"SEFAZ: Conectando em {self.endpoint} para CNPJ {cnpj[:8]}***")
            response = requests.post(
                self.endpoint,
                data=soap_body.encode("utf-8"),
                headers=headers,
                cert=(cert_path, key_path),
                verify=True,           # valida certificado SEFAZ
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
            print(f">>>> RAW HTML/XML SEFAZ <<<<\n{err_msg}\n>>>>>>>>>>>>>>>")
            logger.error(f"SEFAZ: Erro HTTP {e.response.status_code if e.response else 'Unknown'}: {err_msg}")
            raise RuntimeError(f"Erro SEFAZ HTTP {e.response.status_code if e.response else 'Unknown'}: {err_msg[:500]}")
        except requests.exceptions.RequestException as e:
            logger.error(f"SEFAZ: Erro de conexão: {e}")
            raise RuntimeError(f"Erro de conexão com a SEFAZ: {e}")
        finally:
            # Limpa arquivos temporários de certificado
            try:
                os.unlink(cert_path)
                os.unlink(key_path)
            except Exception:
                pass

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
