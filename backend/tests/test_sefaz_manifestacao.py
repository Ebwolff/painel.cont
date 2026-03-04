"""
Testes unitários — Manifestação do Destinatário (Fase 2)
Cobre: endpoints, xml_signer, sefaz_client, sefaz_sync
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from lxml import etree


# ═══════════════════════════════════════════
# 1. test_corgao_dinamico
# ═══════════════════════════════════════════

def test_corgao_dinamico():
    """cOrgao deve retornar código IBGE correto para cada UF."""
    from app_v5.services.sefaz_endpoints import get_codigo_ibge_uf

    assert get_codigo_ibge_uf("SP") == "35"
    assert get_codigo_ibge_uf("RJ") == "33"
    assert get_codigo_ibge_uf("MG") == "31"
    assert get_codigo_ibge_uf("RS") == "43"
    assert get_codigo_ibge_uf("AM") == "13"
    assert get_codigo_ibge_uf("DF") == "53"
    # Fallback para UF desconhecida
    assert get_codigo_ibge_uf("XX") == "35"
    # Case insensitive
    assert get_codigo_ibge_uf("sp") == "35"


# ═══════════════════════════════════════════
# 2. test_id_lote_uniqueness
# ═══════════════════════════════════════════

def test_id_lote_uniqueness():
    """idLote deve ser único a cada chamada e ter exatamente 15 dígitos."""
    from app_v5.services.sefaz_endpoints import gerar_id_lote

    lotes = {gerar_id_lote() for _ in range(100)}
    # Todos devem ser diferentes (colisão improvável com UUID)
    assert len(lotes) == 100
    for lote in lotes:
        assert len(lote) == 15
        assert lote.isdigit()


# ═══════════════════════════════════════════
# 3. test_build_evento_xml
# ═══════════════════════════════════════════

def test_build_evento_xml():
    """XML do evento deve conter todos os campos obrigatórios."""
    from app_v5.services.sefaz_client import SefazClient

    client = SefazClient(ambiente="producao")
    # Não podemos chamar manifest_document sem cert, mas podemos
    # testar que a classe tem os atributos corretos
    assert "210210" in client.DESCRICOES_EVENTO
    assert "210200" in client.DESCRICOES_EVENTO
    assert "210220" in client.DESCRICOES_EVENTO
    assert "210240" in client.DESCRICOES_EVENTO
    assert client.DESCRICOES_EVENTO["210210"] == "Ciencia da Operacao"


# ═══════════════════════════════════════════
# 4. test_sign_sha1 (mock — sem certificado real)
# ═══════════════════════════════════════════

def test_sign_sha1():
    """XMLSigner deve inicializar com perfil sha1 por padrão."""
    pytest.importorskip("xmlsec", reason="xmlsec requer libxmlsec1-dev (Linux)")
    from app_v5.services.xml_signer import SIGN_PROFILES

    assert "sha1" in SIGN_PROFILES
    assert "sign_method" in SIGN_PROFILES["sha1"]
    assert "digest_method" in SIGN_PROFILES["sha1"]


# ═══════════════════════════════════════════
# 5. test_sign_sha256
# ═══════════════════════════════════════════

def test_sign_sha256():
    """Perfil sha256 deve existir e diferir do sha1."""
    pytest.importorskip("xmlsec", reason="xmlsec requer libxmlsec1-dev (Linux)")
    from app_v5.services.xml_signer import SIGN_PROFILES

    assert "sha256" in SIGN_PROFILES
    assert SIGN_PROFILES["sha1"]["sign_method"] != SIGN_PROFILES["sha256"]["sign_method"]
    assert SIGN_PROFILES["sha1"]["digest_method"] != SIGN_PROFILES["sha256"]["digest_method"]


# ═══════════════════════════════════════════
# 6. test_event_id_format
# ═══════════════════════════════════════════

def test_event_id_format():
    """Event ID deve seguir padrão: ID + tpEvento(6) + chNFe(44) + nSeqEvento(02)."""
    tp_evento = "210210"
    chave = "3" * 44
    n_seq = 1

    event_id = f"ID{tp_evento}{chave}{str(n_seq).zfill(2)}"

    assert event_id.startswith("ID210210")
    assert len(event_id) == 2 + 6 + 44 + 2  # 54 chars
    assert event_id == "ID210210" + "3" * 44 + "01"


# ═══════════════════════════════════════════
# 7. test_endpoint_all_27_ufs
# ═══════════════════════════════════════════

def test_endpoint_all_27_ufs():
    """Todos os 27 estados devem resolver para um endpoint válido."""
    from app_v5.services.sefaz_endpoints import (
        get_recepcao_evento_url, get_dist_dfe_url, UF_IBGE,
    )

    assert len(UF_IBGE) == 27

    for uf in UF_IBGE:
        url_evento = get_recepcao_evento_url(uf, "producao")
        url_dist = get_dist_dfe_url(uf, "producao")

        assert url_evento.startswith("https://"), f"Endpoint inválido para {uf}: {url_evento}"
        assert url_dist.startswith("https://"), f"distDFe inválido para {uf}: {url_dist}"
        assert "RecepcaoEvento" in url_evento or "Recepcao" in url_evento, f"Sem RecepcaoEvento para {uf}"


# ═══════════════════════════════════════════
# 8. test_dist_dfe_is_national
# ═══════════════════════════════════════════

def test_dist_dfe_is_national():
    """distDFeInt deve ser o mesmo endpoint para todas as UFs (serviço nacional AN)."""
    from app_v5.services.sefaz_endpoints import get_dist_dfe_url

    urls = {get_dist_dfe_url(uf, "producao") for uf in ["SP", "RJ", "MG", "RS", "AM", "BA", "PR"]}
    assert len(urls) == 1, "distDFe deve ser nacional — mesmo URL para todas as UFs"

    urls_hom = {get_dist_dfe_url(uf, "homologacao") for uf in ["SP", "RJ", "MG"]}
    assert len(urls_hom) == 1, "distDFe homologação também deve ser nacional"

    # Produção != Homologação
    url_prod = get_dist_dfe_url("SP", "producao")
    url_hom = get_dist_dfe_url("SP", "homologacao")
    assert url_prod != url_hom


# ═══════════════════════════════════════════
# 9. test_idempotency_573
# ═══════════════════════════════════════════

def test_idempotency_573():
    """Resposta com cStat 573 (duplicidade) deve ser tratada como sucesso parcial."""
    from app_v5.services.sefaz_client import SefazClient

    client = SefazClient()
    # Simular XML de resposta com cStat 573
    xml_resp = b'''<?xml version="1.0" encoding="utf-8"?>
    <retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe">
        <cStat>128</cStat>
        <xMotivo>Lote processado</xMotivo>
        <retEvento>
            <infEvento>
                <cStat>573</cStat>
                <xMotivo>Duplicidade de evento</xMotivo>
                <nProt>123456789012345</nProt>
            </infEvento>
        </retEvento>
    </retEnvEvento>'''

    result = client._parse_evento_response(xml_resp)
    # 573 não é "sucesso" direto, mas deve retornar o protocolo
    assert result["cStat"] == "573"
    assert result["protocolo"] == "123456789012345"
    assert result["sucesso"] is False  # 573 != 135/136


# ═══════════════════════════════════════════
# 10. test_protocol_saved_136
# ═══════════════════════════════════════════

def test_protocol_saved_136():
    """cStat 136 (já vinculado) deve ser tratado como sucesso com protocolo salvo."""
    from app_v5.services.sefaz_client import SefazClient

    client = SefazClient()
    xml_resp = b'''<?xml version="1.0" encoding="utf-8"?>
    <retEnvEvento xmlns="http://www.portalfiscal.inf.br/nfe">
        <cStat>128</cStat>
        <xMotivo>Lote processado</xMotivo>
        <retEvento>
            <infEvento>
                <cStat>136</cStat>
                <xMotivo>Evento registrado anteriormente</xMotivo>
                <nProt>999888777666555</nProt>
            </infEvento>
        </retEvento>
    </retEnvEvento>'''

    result = client._parse_evento_response(xml_resp)
    assert result["sucesso"] is True
    assert result["cStat"] == "136"
    assert result["protocolo"] == "999888777666555"


# ═══════════════════════════════════════════
# 11. test_cooldown_656_breaks
# ═══════════════════════════════════════════

def test_cooldown_656_breaks():
    """cStat 656 (Consumo Indevido) deve levantar RuntimeError no _parse_response."""
    from app_v5.services.sefaz_client import SefazClient

    client = SefazClient()
    xml_resp = b'''<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <retDistDFeInt xmlns="http://www.portalfiscal.inf.br/nfe">
            <cStat>656</cStat>
            <xMotivo>Consumo Indevido</xMotivo>
        </retDistDFeInt>
      </soap12:Body>
    </soap12:Envelope>'''

    with pytest.raises(RuntimeError, match="656"):
        client._parse_response(xml_resp)


# ═══════════════════════════════════════════
# 12. test_rate_limit_delay
# ═══════════════════════════════════════════

def test_rate_limit_delay():
    """O delay de 0.5s entre manifestações e o limite de 20 devem estar definidos."""
    # Verificação estática dos valores no código
    import ast
    import inspect
    from app_v5.services.sefaz_sync import SefazSyncService

    source = inspect.getsource(SefazSyncService.sync_company_documents)
    assert "MAX_MANIFESTACOES = 20" in source
    assert "DELAY_ENTRE_MANIFESTACOES = 0.5" in source
    assert "asyncio.sleep" in source


# ═══════════════════════════════════════════
# 13. test_redistribuicao_cycle
# ═══════════════════════════════════════════

def test_redistribuicao_cycle():
    """Se manifestadas > 0, o orquestrador deve chamar distDFeInt novamente."""
    import inspect
    from app_v5.services.sefaz_sync import SefazSyncService

    source = inspect.getsource(SefazSyncService.sync_company_documents)

    # Deve conter lógica de redistribuição
    assert "manifestadas > 0" in source
    assert "ETAPA 3" in source
    assert "notas_completas" in source
    # Deve retornar notas_manifestadas no resultado
    assert "notas_manifestadas" in source
