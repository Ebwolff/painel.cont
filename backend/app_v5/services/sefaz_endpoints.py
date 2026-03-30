"""
Mapeamento centralizado de TODOS os endpoints SEFAZ.
Inclui: distDFeInt (AN), RecepcaoEvento4, e utilitários UF/IBGE.
Fonte: Portal Nacional NF-e (www.nfe.fazenda.gov.br)
"""
import uuid

# ═══════════════════════════════════════════════
# Código IBGE por UF (27 estados)
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
# Serviço Nacional (AN) — mesmo endpoint para todas as UFs
# ═══════════════════════════════════════════════

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
# RecepcaoEvento4 (manifestação do destinatário)
# ═══════════════════════════════════════════════

RECEPCAO_EVENTO_PROPRIO = {
    "producao": {
        "AM": "https://nfe.sefaz.am.gov.br/services2/services/RecepcaoEvento4",
        "BA": "https://nfe.sefaz.ba.gov.br/webservices/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx",
        "GO": "https://nfe.sefaz.go.gov.br/nfe/services/NFeRecepcaoEvento4",
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

# Estados que usam SVRS para RecepcaoEvento
ESTADOS_SVRS = {
    "AC", "AL", "AP", "CE", "DF", "ES", "MA", "PA", "PB",
    "PI", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "TO",
}


def get_recepcao_evento_url(uf: str, ambiente: str = "producao") -> str:
    """
    Resolve endpoint RecepcaoEvento4 para uma UF e ambiente.
    NOTA: Para Eventos de Manifestação do Destinatário, SEMPRE envia para AN, 
    independentemente da UF da empresa, pois cOrgao=91.
    """
    if ambiente == "producao":
        return "https://www.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"
    return "https://hom.nfe.fazenda.gov.br/NFeRecepcaoEvento4/NFeRecepcaoEvento4.asmx"
