# Manifestação do Destinatário — Plano de Implementação Completo

> **Classificação:** Requisito Funcional Crítico (não é melhoria)  
> **Motivo:** Sem manifestação, a SEFAZ nunca libera o XML completo (`procNFe`)  
> **Posição no roadmap:** Nova **Fase 2** (antes da antiga Fase 2 de segurança)

---

## 1. Visão Geral do Fluxo

```
[1] distDFeInt (ultNSU=X)
     └─→ SEFAZ retorna 50x resNFe (resumos)
           └─→ Salva no banco com manifestado=false

[2] Para cada resNFe NÃO manifestado:
     └─→ Monta XML envEvento (tipo 210210)
     └─→ Assina com XMLDSIG (certificado A1)
     └─→ Envia para RecepcaoEvento4 (endpoint por UF)
     └─→ Salva protocolo + status no banco

[3] distDFeInt (ultNSU=Y)  ← rodado depois, em outra chamada
     └─→ SEFAZ retorna procNFe (XMLs completos)
     └─→ Parser extrai itens, impostos, CFOP
     └─→ Rule Engine valida CBS/IBS
```

---

## 2. Arquivos Impactados

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `sefaz_client.py` | MODIFY | Novo método `manifest_document()` + resolução de endpoint por UF |
| `sefaz_sync.py` | MODIFY | Orquestração: resNFe → manifestação → reprocessamento |
| `xml_signer.py` | **NEW** | Assinatura XMLDSIG com lxml + xmlsec1 |
| `sefaz_endpoints.py` | **NEW** | Mapeamento UF → endpoint (RecepcaoEvento + DistDFe) |
| `requirements.txt` | MODIFY | Adicionar `xmlsec` e `requests-pkcs12` |
| `019_manifestacao.sql` | **NEW** | Migração: campos de manifestação na tabela |

---

## 3. Mapeamento de Endpoints por UF

### [NEW] sefaz_endpoints.py

```python
"""
Mapeamento oficial SEFAZ — Endpoints RecepcaoEvento4 por autorizador.
Fonte: Portal Nacional NF-e (www.nfe.fazenda.gov.br)
"""

# Estados com autorizador próprio
RECEPCAO_EVENTO_PROPRIO = {
    "AM": "https://nfe.sefaz.am.gov.br/services2/services/RecepcaoEvento4",
    "BA": "https://nfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
    "GO": "https://nfe.sefaz.go.gov.br/nfe/services/RecepcaoEvento4",
    "MG": "https://nfe.sefaz.mg.gov.br/nfe/services/NFeRecepcaoEvento4",
    "MS": "https://nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4",
    "MT": "https://nfe.sefaz.mt.gov.br/nfews/v2/services/NFeRecepcaoEvento4",
    "PE": "https://nfe.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4",
    "PR": "https://nfe.sefaz.pr.gov.br/nfe/NFeRecepcaoEvento4",
    "SP": "https://nfe.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4.asmx",
}

# SVRS atende: AC, AL, AP, CE, DF, ES, PA, PB, PI, RJ, RN, RO, RR, RS, SC, SE, TO
SVRS_PRODUCAO = "https://nfe.svrs.rs.gov.br/ws/NfeRecepcaoEvento4.asmx"
SVRS_HOMOLOGACAO = "https://nfe-homologacao.svrs.rs.gov.br/ws/NfeRecepcaoEvento4.asmx"

# Homologação para autorizadores próprios
RECEPCAO_EVENTO_PROPRIO_HOM = {
    "AM": "https://homnfe.sefaz.am.gov.br/services2/services/RecepcaoEvento4",
    "BA": "https://hnfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
    "GO": "https://homolog.sefaz.go.gov.br/nfe/services/RecepcaoEvento4",
    "MG": "https://hnfe.sefaz.mg.gov.br/nfe/services/NFeRecepcaoEvento4",
    "MS": "https://hom.nfe.sefaz.ms.gov.br/ws/NFeRecepcaoEvento4",
    "MT": "https://homologacao.sefaz.mt.gov.br/nfews/v2/services/NFeRecepcaoEvento4",
    "PE": "https://nfe-homologacao.sefaz.pe.gov.br/nfe-service/services/NFeRecepcaoEvento4",
    "PR": "https://homologacao.nfe.sefaz.pr.gov.br/nfe/NFeRecepcaoEvento4",
    "SP": "https://homologacao.nfe.fazenda.sp.gov.br/ws/NFeRecepcaoEvento4.asmx",
}

ESTADOS_SVRS = {"AC","AL","AP","CE","DF","ES","PA","PB","PI","RJ","RN","RO","RR","RS","SC","SE","TO"}

def get_recepcao_evento_url(uf: str, ambiente: str = "producao") -> str:
    """Resolve o endpoint RecepcaoEvento4 para uma UF e ambiente."""
    if ambiente == "homologacao":
        if uf in RECEPCAO_EVENTO_PROPRIO_HOM:
            return RECEPCAO_EVENTO_PROPRIO_HOM[uf]
        return SVRS_HOMOLOGACAO
    
    if uf in RECEPCAO_EVENTO_PROPRIO:
        return RECEPCAO_EVENTO_PROPRIO[uf]
    return SVRS_PRODUCAO
```

---

## 4. Assinatura Digital XMLDSIG

### [NEW] xml_signer.py

**Dependência:** `pip install xmlsec lxml`

```python
"""
Assinatura digital XMLDSIG para eventos SEFAZ.
Padrão: Enveloped Signature, C14N Exclusive, SHA-1 (exigido pela SEFAZ).
"""
import xmlsec
from lxml import etree
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

NFE_NS = "http://www.portalfiscal.inf.br/nfe"


class XMLSigner:
    def __init__(self, pfx_bytes: bytes, password: str):
        pw = password.encode("utf-8") if isinstance(password, str) else password
        self.private_key, self.certificate, self.chain = load_key_and_certificates(pfx_bytes, pw)
    
    def sign_event(self, xml_element, reference_id):
        """
        Assina um elemento XML (infEvento) com Enveloped Signature.
        reference_id: valor do atributo Id do infEvento (ex: "ID210210...")
        Retorna o elemento com <Signature> inserido.
        """
        # 1. Criar template de assinatura
        sig_node = xmlsec.template.create(
            xml_element,
            c14n_method=xmlsec.constants.TransformExclC14N,
            sign_method=xmlsec.constants.TransformRsaSha1,
            ns="ds",
        )
        
        # 2. Reference apontando para o Id do infEvento
        ref = xmlsec.template.add_reference(
            sig_node,
            digest_method=xmlsec.constants.TransformSha1,
            uri=f"#{reference_id}",
        )
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformEnveloped)
        xmlsec.template.add_transform(ref, xmlsec.constants.TransformExclC14N)
        
        # 3. KeyInfo com X509Data
        key_info = xmlsec.template.ensure_key_info(sig_node)
        x509_data = xmlsec.template.add_x509_data(key_info)
        xmlsec.template.x509_data_add_certificate(x509_data)
        
        # 4. Inserir Signature no XML
        xml_element.append(sig_node)
        
        # 5. Carregar chave privada e certificado
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

## 5. Método manifest_document() no SefazClient

### [MODIFY] sefaz_client.py

```python
from app_v5.services.xml_signer import XMLSigner
from app_v5.services.sefaz_endpoints import get_recepcao_evento_url

SOAP_ACTION_EVENTO = "http://www.portalfiscal.inf.br/nfe/wsdl/NFeRecepcaoEvento4/nfeRecepcaoEvento"


def manifest_document(
    self,
    pfx_bytes, password, cnpj, chave_nfe, uf_empresa,
    n_seq_evento=1, tp_evento="210210",
):
    """
    Envia evento de Manifestação do Destinatário para uma NF-e.
    
    tp_evento:
        210200 = Confirmação da Operação
        210210 = Ciência da Operação  ← default (primeiro passo)
        210220 = Desconhecimento da Operação
        210240 = Operação não Realizada
    
    Retorna: {"sucesso": bool, "protocolo": str, "cStat": str, "xMotivo": str}
    """
    cnpj_limpo = cnpj.replace(".", "").replace("/", "").replace("-", "")
    tp_amb = "1" if self.ambiente == "producao" else "2"
    c_orgao = "91"  # AN para eventos de manifestação
    
    event_id = f"ID{tp_evento}{chave_nfe}{str(n_seq_evento).zfill(2)}"
    
    from datetime import datetime, timezone
    dh_evento = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S-00:00")
    
    descricoes = {
        "210200": "Confirmacao da Operacao",
        "210210": "Ciencia da Operacao",
        "210220": "Desconhecimento da Operacao",
        "210240": "Operacao nao Realizada",
    }
    
    # 1. Montar XML → 2. Assinar → 3. Envelope SOAP → 4. Enviar mTLS
    # (ver código completo no implementation_plan.md)
```

---

## 6. Migração de Banco de Dados

### [NEW] 019_manifestacao.sql

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

## 7. Tratamento de Erros Específicos

| cStat | Significado | Ação |
|-------|------------|------|
| **135** | Evento registrado com sucesso | ✅ Marcar `manifestado=true`, salvar protocolo |
| **136** | Evento já vinculado previamente | ✅ Marcar `manifestado=true` (idempotente) |
| **573** | Duplicidade de Evento | ✅ Marcar `manifestado=true` (já foi feito) |
| **580** | Evento fora do prazo | ⚠️ Log warning, não manifestar |
| **217** | NF-e não consta na base | ⚠️ Log, marcar nota para revisão |
| **656** | Consumo Indevido | 🛑 Parar loop, aplicar cooldown 65min |

---

## 8. Dependências Novas

```txt
# requirements.txt (adicionar)
xmlsec>=1.3.13          # Assinatura XMLDSIG
requests-pkcs12>=1.24   # mTLS sem tmpfiles
```

Pré-requisito Railway: `libxmlsec1-dev` no container.

```toml
# nixpacks.toml
[phases.setup]
aptPkgs = ["libxmlsec1-dev", "pkg-config"]
```

---

## 9. Roadmap Atualizado

### Fase 1 — Estabilidade (Esta semana)
| Tarefa | Esforço |
|--------|---------|
| Backoff erro 656 | 30 min |
| Validar expiração cert | 15 min |
| Lock deduplicação | 20 min |

### Fase 2 — Manifestação (NOVA — Obrigatória ~5h)
| Tarefa | Esforço |
|--------|---------|
| `sefaz_endpoints.py` (UF) | 30 min |
| `xml_signer.py` (XMLDSIG) | 1h |
| `manifest_document()` | 1h |
| Migração SQL | 15 min |
| Orquestrador | 1h |
| Config Railway | 15 min |
| Testes unitários | 1h |

### Fase 3 — Segurança
| Tarefa | Esforço |
|--------|---------|
| requests_pkcs12 | 30 min |
| TLS 1.2 | 10 min |
| RLS cert | 10 min |

### Fase 4 — Escala
| Tarefa | Esforço |
|--------|---------|
| Worker ARQ/Redis | 2h |
| Service Layer | 2h |

---

## 10. Pontos de Teste Unitário

| Teste | O que valida |
|-------|-------------|
| `test_build_evento_xml` | Estrutura XML do envEvento conforme layout 1.00 |
| `test_sign_event` | Assinatura XMLDSIG gera DigestValue e SignatureValue válidos |
| `test_event_id_format` | ID = `ID` + tpEvento(6) + chNFe(44) + nSeqEvento(2) |
| `test_endpoint_resolution` | Cada UF resolve para endpoint correto (prod/hom) |
| `test_idempotency_573` | cStat 573 marca `manifestado=true` sem erro |
| `test_cooldown_656` | cStat 656 para o loop e não manifesta mais |
| `test_manifest_flow` | Mock: resNFe → manifestação → marcação no banco |
