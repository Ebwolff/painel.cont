# Manifestação do Destinatário — Plano Revisado (v2)

> **7 correções técnicas aplicadas** sobre o plano original  
> **Classificação:** Requisito Funcional Crítico  
> Data: 04/03/2026

---

## Correções Aplicadas

| # | Correção | Status |
|---|---------|:------:|
| 1 | cOrgao dinâmico por UF (não fixo 91) | ✅ |
| 2 | idLote via UUID truncado | ✅ |
| 3 | Redistribuição pós-manifestação no mesmo ciclo | ✅ |
| 4 | Rate limiting 500ms + teto 20 eventos | ✅ |
| 5 | Centralizar endpoints distDFe + RecepcaoEvento | ✅ |
| 6 | XMLSigner preparável para SHA-256 | ✅ |
| 7 | Persistir protocolo em 136/573 | ✅ |

---

## 1. Fluxo Técnico Revisado

```
ETAPA 1 → distDFeInt (ultNSU=X)
           └─→ Recebe resNFe (resumos)
           └─→ Salva no banco (manifestado=false, is_resumo=true)

ETAPA 2 → Para cada resNFe NÃO manifestado (máx 20):
           └─→ Monta envEvento (210210)
           └─→ Assina XMLDSIG (cert A1)
           └─→ Envia para RecepcaoEvento4 (endpoint por UF)
           └─→ Salva protocolo no banco
           └─→ asyncio.sleep(0.5)  ← rate limiting
           └─→ Se cStat=656 → BREAK imediato

ETAPA 3 → SE manifestadas > 0:
           └─→ Nova chamada distDFeInt (mesmo ultNSU)
           └─→ SEFAZ retorna procNFe (XMLs completos)
           └─→ Parser extrai itens, impostos, CFOP
           └─→ Rule Engine valida CBS/IBS
           └─→ Atualiza nota existente (is_resumo → false)

ETAPA 4 → Atualiza ultimo_nsu no banco
```

---

## 2. Arquivos Impactados

| Arquivo | Ação |
|---------|------|
| `sefaz_endpoints.py` | **NEW** — Endpoints distDFe + RecepcaoEvento + `get_codigo_ibge_uf()` |
| `xml_signer.py` | **NEW** — XMLDSIG com suporte SHA-1/SHA-256 |
| `sefaz_client.py` | **MODIFY** — `manifest_document()` + usar endpoints centralizados |
| `sefaz_sync.py` | **MODIFY** — Orquestração 4 etapas + rate limiting |
| `019_manifestacao.sql` | **NEW** — Migração SQL |
| `requirements.txt` | **MODIFY** — `xmlsec`, `requests-pkcs12` |
| `nixpacks.toml` | **MODIFY** — `libxmlsec1-dev` |

---

## 3. [NEW] sefaz_endpoints.py

```python
"""
Mapeamento centralizado de TODOS os endpoints SEFAZ.
Fonte: Portal Nacional NF-e (www.nfe.fazenda.gov.br)
"""
import uuid

# ═══════════════════════════════════════════════
# Código IBGE por UF
# ═══════════════════════════════════════════════

UF_IBGE = {
    "AC": "12", "AL": "27", "AP": "16", "AM": "13", "BA": "29",
    "CE": "23", "DF": "53", "ES": "32", "GO": "52", "MA": "21",
    "MT": "51", "MS": "50", "MG": "31", "PA": "15", "PB": "25",
    "PR": "41", "PE": "26", "PI": "22", "RJ": "33", "RN": "24",
    "RS": "43", "RO": "11", "RR": "14", "SC": "42", "SP": "35",
    "SE": "28", "TO": "17",
}

def get_codigo_ibge_uf(uf: str) -> str:
    """Retorna código IBGE de 2 dígitos para a UF. Fallback: 35 (SP)."""
    return UF_IBGE.get(uf.upper(), "35")


def gerar_id_lote() -> str:
    """Gera idLote único e seguro (UUID truncado a 15 dígitos)."""
    return str(uuid.uuid4().int)[:15]


# ═══════════════════════════════════════════════
# DistribuicaoDFe (distDFeInt)
# ═══════════════════════════════════════════════

# distDFeInt é SEMPRE Ambiente Nacional (AN), endpoint único
DIST_DFE_PRODUCAO = "https://www1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"
DIST_DFE_HOMOLOGACAO = "https://hom1.nfe.fazenda.gov.br/NFeDistribuicaoDFe/NFeDistribuicaoDFe.asmx"

def get_dist_dfe_url(uf: str, ambiente: str = "producao") -> str:
    """
    Resolve endpoint distDFeInt.
    NOTA: Este serviço é nacional (AN) — mesmo endpoint para todas as UFs.
    O parâmetro `uf` é aceito por consistência de API mas não altera o resultado.
    """
    return DIST_DFE_PRODUCAO if ambiente == "producao" else DIST_DFE_HOMOLOGACAO


# ═══════════════════════════════════════════════
# RecepcaoEvento4 (manifestação)
# ═══════════════════════════════════════════════

RECEPCAO_EVENTO_PROPRIO = {
    "producao": {
        "AM": "https://nfe.sefaz.am.gov.br/services2/services/RecepcaoEvento4",
        "BA": "https://nfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
        "GO": "https://nfe.sefaz.go.gov.br/nfe/services/RecepcaoEvento4",
        "MG": "https://nfe.sefaz.mg.gov.br/nfe/services/NFeRecepcaoEvento4",
        "MS": "https://nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4",
        "MT": "https://nfe.sefaz.mt.gov.br/nfews/v2/services/NFeRecepcaoEvento4",
        "PE": "https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4",
        "PR": "https://nfe.sefaz.pr.gov.br/nfe/NFeRecepcaoEvento4",
        "SP": "https://nfe.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4.asmx",
    },
    "homologacao": {
        "AM": "https://homnfe.sefaz.am.gov.br/services2/services/RecepcaoEvento4",
        "BA": "https://hnfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
        "GO": "https://homolog.sefaz.go.gov.br/nfe/services/RecepcaoEvento4",
        "MG": "https://hnfe.sefaz.mg.gov.br/nfe/services/NFeRecepcaoEvento4",
        "MS": "https://hom.nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4",
        "MT": "https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NFeRecepcaoEvento4",
        "PE": "https://nfe-homologacao.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4",
        "PR": "https://homologacao.nfe.sefaz.pr.gov.br/nfe/NFeRecepcaoEvento4",
        "SP": "https://homologacao.nfe.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4.asmx",
    },
}

SVRS = {
    "producao": "https://nfe.svrs.rs.gov.br/ws/NfeRecepcaoEvento4.asmx",
    "homologacao": "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeRecepcaoEvento4.asmx",
}

ESTADOS_SVRS = {"AC","AL","AP","CE","DF","ES","PA","PB","PI","RJ","RN","RO","RR","RS","SC","SE","TO"}


def get_recepcao_evento_url(uf: str, ambiente: str = "producao") -> str:
    """Resolve endpoint RecepcaoEvento4 para uma UF e ambiente."""
    uf = uf.upper()
    endpoints = RECEPCAO_EVENTO_PROPRIO.get(ambiente, {})
    if uf in endpoints:
        return endpoints[uf]
    return SVRS.get(ambiente, SVRS["producao"])
```

---

## 4. [NEW] xml_signer.py — Com suporte SHA-256

```python
"""
Assinatura digital XMLDSIG para eventos SEFAZ.
Padrão atual: SHA-1 (exigido pela SEFAZ).
Preparado para migração futura para SHA-256.
"""
import xmlsec
from lxml import etree
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption


# Perfis de assinatura suportados
SIGN_PROFILES = {
    "sha1": {
        "sign_method": xmlsec.constants.TransformRsaSha1,
        "digest_method": xmlsec.constants.TransformSha1,
    },
    "sha256": {
        "sign_method": xmlsec.constants.TransformRsaSha256,
        "digest_method": xmlsec.constants.TransformSha256,
    },
}


class XMLSigner:
    def __init__(self, pfx_bytes: bytes, password: str, profile: str = "sha1"):
        """
        profile: "sha1" (padrão SEFAZ atual) ou "sha256" (futuro).
        """
        pw = password.encode("utf-8") if isinstance(password, str) else password
        self.private_key, self.certificate, self.chain = load_key_and_certificates(pfx_bytes, pw)
        
        if profile not in SIGN_PROFILES:
            raise ValueError(f"Perfil '{profile}' inválido. Use: {list(SIGN_PROFILES.keys())}")
        self.profile = SIGN_PROFILES[profile]

    def sign_event(self, xml_element: etree._Element, reference_id: str) -> etree._Element:
        """
        Assina um elemento <evento> com Enveloped Signature.
        reference_id: atributo Id do <infEvento> (ex: "ID210210...").
        """
        # 1. Template de assinatura (perfil configurável)
        sig_node = xmlsec.template.create(
            xml_element,
            c14n_method=xmlsec.constants.TransformExclC14N,
            sign_method=self.profile["sign_method"],
            ns="ds",
        )

        # 2. Reference → aponta para o Id do infEvento
        ref = xmlsec.template.add_reference(
            sig_node,
            digest_method=self.profile["digest_method"],
            uri=f"#{reference_id}",
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)

        # 3. KeyInfo → X509Data com certificado
        key_info = xmlsec.template.ensure_key_info(sig_node)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_certificate(x509_data)

        # 4. Inserir Signature no XML
        xml_element.append(sig_node)

        # 5. Carregar chave + cert
        cert_pem = self.certificate.public_bytes(Encoding.PEM)
        key_pem = self.private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())

        ctx = xmlsec.SignatureContext()
        ctx.key = xmlsec.Key.from_memory(key_pem, xmlsec.constants.KeyDataFormatPem)
        ctx.key.load_cert(cert_pem, xmlsec.constants.KeyDataFormatPem)

        # 6. Assinar
        ctx.sign(sig_node)
        return xml_element
```

---

## 5. [MODIFY] sefaz_client.py — `manifest_document()` corrigido

```python
from app_v5.services.xml_signer import XMLSigner
from app_v5.services.sefaz_endpoints import (
    get_recepcao_evento_url, get_dist_dfe_url,
    get_codigo_ibge_uf, gerar_id_lote,
)

SOAP_ACTION_EVENTO = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"
)

NFE_NS = "http://www.portalfiscal.inf.br/nfe"


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
    Envia evento de Manifestação do Destinatário.

    Retorna: {
        "sucesso": bool,
        "protocolo": str | None,
        "cStat": str,
        "xMotivo": str,
    }
    """
    cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
    tp_amb = "1" if self.ambiente == "producao" else "2"

    # ═══ CORREÇÃO 1: cOrgao dinâmico por UF ═══
    c_orgao = get_codigo_ibge_uf(uf_empresa)

    event_id = f"ID{tp_evento}{chave_nfe}{str(n_seq_evento).zfill(2)}"

    from datetime import datetime, timezone
    dh_evento = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S-00:00")

    descricoes = {
        "210200": "Confirmacao da Operacao",
        "210210": "Ciencia da Operacao",
        "210220": "Desconhecimento da Operacao",
        "210240": "Operacao nao Realizada",
    }
    x_evento = descricoes.get(tp_evento, "Ciencia da Operacao")

    # ── 1. Montar XML do evento ──
    evento = etree.Element("evento", versao="1.00", xmlns=NFE_NS)
    inf = etree.SubElement(evento, "infEvento", Id=event_id)

    etree.SubElement(inf, "cOrgao").text = c_orgao      # ← dinâmico
    etree.SubElement(inf, "tpAmb").text = tp_amb
    etree.SubElement(inf, "CNPJ").text = cnpj_limpo
    etree.SubElement(inf, "chNFe").text = chave_nfe
    etree.SubElement(inf, "dhEvento").text = dh_evento
    etree.SubElement(inf, "tpEvento").text = tp_evento
    etree.SubElement(inf, "nSeqEvento").text = str(n_seq_evento)
    etree.SubElement(inf, "verEvento").text = "1.00"

    det = etree.SubElement(inf, "detEvento", versao="1.00")
    etree.SubElement(det, "descEvento").text = x_evento

    # ── 2. Assinar XML ──
    signer = XMLSigner(pfx_bytes, password)  # profile="sha1" por padrão
    evento_assinado = signer.sign_event(evento, event_id)

    # ── 3. Envelope envEvento ──
    env = etree.Element("envEvento", versao="1.00", xmlns=NFE_NS)

    # ═══ CORREÇÃO 2: idLote via UUID truncado ═══
    etree.SubElement(env, "idLote").text = gerar_id_lote()
    env.append(evento_assinado)

    xml_str = etree.tostring(env, xml_declaration=True, encoding="UTF-8").decode()

    # ── 4. SOAP 1.2 Envelope ──
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
        "Content-Type": f'application/soap+xml; charset=utf-8; action="{SOAP_ACTION_EVENTO}"',
    }

    # ── 5. Enviar mTLS ──
    from requests_pkcs12 import post as pkcs12_post

    response = pkcs12_post(
        endpoint,
        data=soap.encode("utf-8"),
        headers=headers,
        pkcs12_data=pfx_bytes,
        pkcs12_password=password,
        verify=True,
        timeout=self.timeout,
    )
    response.raise_for_status()

    return self._parse_evento_response(response.content)


def _parse_evento_response(self, xml_bytes: bytes) -> dict:
    """Parseia resposta do RecepcaoEvento4."""
    root = etree.fromstring(xml_bytes)

    cstat_el = root.xpath("//*[local-name()='cStat']")
    xmot_el = root.xpath("//*[local-name()='xMotivo']")
    nprot_el = root.xpath("//*[local-name()='nProt']")

    cstat = cstat_el[0].text if cstat_el else "?"
    xmotivo = xmot_el[0].text if xmot_el else ""
    protocolo = nprot_el[0].text if nprot_el else None  # ← pode ser None

    sucesso = cstat in ("135", "136")

    return {
        "sucesso": sucesso,
        "cStat": cstat,
        "xMotivo": xmotivo,
        "protocolo": protocolo,
    }
```

---

## 6. [MODIFY] sefaz_sync.py — Orquestração 4 Etapas

```python
import asyncio
from datetime import datetime, timezone

MAX_MANIFESTACOES_POR_CICLO = 20
DELAY_ENTRE_MANIFESTACOES = 0.5  # segundos


async def sync_company_documents(self, empresa_id, tenant_id):
    # ... (carregar cert, cnpj, uf — existente) ...

    sefaz = SefazClient(ambiente=ambiente)

    # ═══════════════════════════════════════════
    # ETAPA 1: Buscar novos documentos
    # ═══════════════════════════════════════════
    documentos = sefaz.call_sefaz(pfx_bytes, senha, cnpj, ultimo_nsu, codigo_uf)

    for doc in documentos:
        nfe_data = self.parser.parse_nfe(doc["xml_content"])
        is_resumo = nfe_data.get("is_resumo", False)

        if is_resumo:
            validation_result = {
                "status": "pendente_manifestacao",
                "alertas": [],
                "validation_details": {"cbs_ok": None, "ibs_ok": None},
                "items_results": [],
            }
        else:
            validation_result = self.rule_engine.validate_nfe(nfe_data)

        nota_id = self.supabase.insert_nfe_result(
            nfe_data, validation_result,
            tenant_id=tenant_id, empresa_id=empresa_id,
        )

        # Marcar como resumo no banco
        if is_resumo:
            admin_client.table("notas_fiscais").update({
                "is_resumo": True,
                "manifestado": False,
            }).eq("id", nota_id).execute()

        if doc["nsu"] > novo_nsu:
            novo_nsu = doc["nsu"]
        notas_ok += 1

    # ═══════════════════════════════════════════
    # ETAPA 2: Manifestar pendentes (rate limited)
    # ═══════════════════════════════════════════
    pendentes = admin_client.table("notas_fiscais") \
        .select("id, chave_acesso, n_seq_evento") \
        .eq("empresa_id", empresa_id) \
        .eq("is_resumo", True) \
        .eq("manifestado", False) \
        .limit(MAX_MANIFESTACOES_POR_CICLO) \
        .execute()

    manifestadas = 0
    hit_656 = False

    for nota in (pendentes.data or []):
        chave = nota.get("chave_acesso")
        if not chave or len(chave) != 44:
            continue

        try:
            result = sefaz.manifest_document(
                pfx_bytes=pfx_bytes,
                password=senha,
                cnpj=cnpj,
                chave_nfe=chave,
                uf_empresa=uf_sigla,
                n_seq_evento=nota.get("n_seq_evento", 1),
            )

            if result["sucesso"]:
                # cStat 135 ou 136 — evento aceito
                admin_client.table("notas_fiscais").update({
                    "manifestado": True,
                    "tipo_manifestacao": "210210",
                    "protocolo_evento": result["protocolo"],  # ═══ CORREÇÃO 7
                    "data_manifestacao": datetime.now(timezone.utc).isoformat(),
                }).eq("id", nota["id"]).execute()
                manifestadas += 1

            elif result["cStat"] == "573":
                # Duplicidade — já manifestado, salvar protocolo se houver
                admin_client.table("notas_fiscais").update({
                    "manifestado": True,
                    "tipo_manifestacao": "210210",
                    "protocolo_evento": result["protocolo"],  # ═══ CORREÇÃO 7
                }).eq("id", nota["id"]).execute()
                manifestadas += 1

            elif result["cStat"] == "656":
                logger.warning("SEFAZ 656: Consumo Indevido na manifestação. Parando.")
                hit_656 = True
                break  # ═══ CORREÇÃO 4: parar imediatamente

            elif result["cStat"] == "580":
                logger.warning(f"Evento fora de prazo para {chave[:20]}")

            elif result["cStat"] == "217":
                logger.warning(f"NF-e não consta na base SEFAZ: {chave[:20]}")

        except Exception as e:
            logger.error(f"Erro ao manifestar {chave[:20]}: {e}")

        # ═══ CORREÇÃO 4: delay entre chamadas ═══
        await asyncio.sleep(DELAY_ENTRE_MANIFESTACOES)

    # ═══════════════════════════════════════════
    # ETAPA 3: Redistribuição pós-manifestação
    # ═══════════════════════════════════════════
    notas_completas = 0
    if manifestadas > 0 and not hit_656:
        logger.info(f"SEFAZ SYNC: {manifestadas} notas manifestadas. Buscando XMLs completos...")

        try:
            docs_completos = sefaz.call_sefaz(pfx_bytes, senha, cnpj, novo_nsu, codigo_uf)

            for doc in docs_completos:
                nfe_data = self.parser.parse_nfe(doc["xml_content"])
                is_resumo = nfe_data.get("is_resumo", False)

                if not is_resumo:
                    # XML completo! Processar com rule engine
                    validation_result = self.rule_engine.validate_nfe(nfe_data)
                    chave = nfe_data.get("chave_acesso")

                    # Atualizar nota existente (era resumo → agora completa)
                    existing = admin_client.table("notas_fiscais") \
                        .select("id") \
                        .eq("chave_acesso", chave) \
                        .eq("empresa_id", empresa_id) \
                        .maybe_single().execute()

                    if existing and existing.data:
                        # Atualizar nota existente com dados completos
                        admin_client.table("notas_fiscais").update({
                            "is_resumo": False,
                            "emitente_cnpj": nfe_data.get("emitente_cnpj"),
                            "emitente_nome": nfe_data.get("emitente_nome"),
                            "valor_total": nfe_data.get("valor_total"),
                            "valor_cbs": nfe_data.get("valor_cbs"),
                            "valor_ibs": nfe_data.get("valor_ibs"),
                            "numero": nfe_data.get("numero"),
                            "serie": nfe_data.get("serie"),
                            "data_emissao": nfe_data.get("data_emissao"),
                            "status": validation_result["status"],
                        }).eq("id", existing.data["id"]).execute()

                        # Inserir itens
                        nota_id = existing.data["id"]
                        for item in nfe_data.get("itens", []):
                            admin_client.table("nfe_items").insert({
                                "tenant_id": tenant_id,
                                "nota_fiscal_id": nota_id,
                                "n_item": item.get("n_item"),
                                "ncm": item.get("ncm"),
                                "cfop": item.get("cfop"),
                                "v_prod": item.get("v_prod"),
                                "v_cbs": item.get("v_cbs"),
                                "v_ibs": item.get("v_ibs"),
                            }).execute()

                        notas_completas += 1
                    else:
                        # Nota nova (não era resumo anterior)
                        self.supabase.insert_nfe_result(
                            nfe_data, validation_result,
                            tenant_id=tenant_id, empresa_id=empresa_id,
                        )
                        notas_completas += 1

                if doc["nsu"] > novo_nsu:
                    novo_nsu = doc["nsu"]

        except Exception as e:
            logger.error(f"SEFAZ SYNC: Erro na redistribuição pós-manifestação: {e}")

    # ═══════════════════════════════════════════
    # ETAPA 4: Atualizar NSU + timestamp
    # ═══════════════════════════════════════════
    admin_client.table("certificados_a1").update({
        "ultimo_nsu": novo_nsu,
        "ultimo_sync": datetime.now(timezone.utc).isoformat(),
        "status": "ativo",
    }).eq("empresa_id", empresa_id).execute()

    return {
        "status": "success",
        "notas_resumo": notas_ok,
        "notas_manifestadas": manifestadas,
        "notas_completas": notas_completas,
        "novo_nsu": novo_nsu,
    }
```

---

## 7. [NEW] 019_manifestacao.sql

```sql
ALTER TABLE notas_fiscais
  ADD COLUMN IF NOT EXISTS manifestado BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS tipo_manifestacao TEXT,
  ADD COLUMN IF NOT EXISTS protocolo_evento TEXT,
  ADD COLUMN IF NOT EXISTS data_manifestacao TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS n_seq_evento INT DEFAULT 1,
  ADD COLUMN IF NOT EXISTS is_resumo BOOLEAN DEFAULT false;

CREATE INDEX IF NOT EXISTS idx_notas_manifestacao_pendente
  ON notas_fiscais (empresa_id, manifestado)
  WHERE manifestado = false AND is_resumo = true;
```

---

## 8. Tratamento de Erros

| cStat | Ação | Protocolo |
|-------|------|:---------:|
| **135** | ✅ `manifestado=true` | Salvar |
| **136** | ✅ `manifestado=true` | Salvar (se houver) |
| **573** | ✅ `manifestado=true` (duplicidade) | Salvar (se houver) |
| **580** | ⚠️ Log, não manifestar | — |
| **217** | ⚠️ Log, marcar revisão | — |
| **656** | 🛑 `break` imediato, cooldown 65min | — |

---

## 9. Dependências

```txt
# requirements.txt
xmlsec>=1.3.13
requests-pkcs12>=1.24
```

```toml
# nixpacks.toml
[phases.setup]
aptPkgs = ["libxmlsec1-dev", "pkg-config"]
```

---

## 10. Testes Unitários Atualizados

| Teste | Valida |
|-------|--------|
| `test_corgao_dinamico` | `get_codigo_ibge_uf("SP")` → `"35"`, `("MG")` → `"31"` |
| `test_id_lote_uniqueness` | 1000 chamadas `gerar_id_lote()` → 0 colisões |
| `test_build_evento_xml` | Estrutura XML conforme layout 1.00 |
| `test_sign_sha1` | Assinatura com profile `"sha1"` produz DigestValue válido |
| `test_sign_sha256` | Assinatura com profile `"sha256"` produz DigestValue válido |
| `test_event_id_format` | ID = `ID` + tpEvento(6) + chNFe(44) + nSeqEvento(2) = 52 chars |
| `test_endpoint_all_27_ufs` | Cada UF resolve para URL válida (prod + hom) |
| `test_dist_dfe_is_national` | `get_dist_dfe_url("SP")` == `get_dist_dfe_url("RS")` |
| `test_idempotency_573` | cStat 573 → `manifestado=true` + protocolo salvo |
| `test_protocol_saved_136` | cStat 136 → protocolo salvo (se presente) |
| `test_cooldown_656_breaks` | cStat 656 → loop para, retorna parcial |
| `test_rate_limit_delay` | 20 chamadas → ≥10s de elapsed time |
| `test_redistribuicao_cycle` | Mock: resNFe → manifest → procNFe no mesmo ciclo |

---

## 11. Estimativa Revisada

| Tarefa | Esforço Original | Esforço Revisado | Delta |
|--------|:----------------:|:----------------:|:-----:|
| `sefaz_endpoints.py` | 30 min | **45 min** | +15 (distDFe + IBGE) |
| `xml_signer.py` | 1h | **1h15** | +15 (perfis SHA) |
| `manifest_document()` | 1h | 1h | — |
| Migração SQL | 15 min | 15 min | — |
| Orquestrador 4 etapas | 1h | **2h** | +1h (redistribuição) |
| Config Railway | 15 min | 15 min | — |
| Testes unitários | 1h | **1h30** | +30 (novos testes) |
| **Total** | **~5h** | **~6h30** | **+1h30** |

---

> Plano revisado e pronto para implementação.
