import pytest
from app_v5.services.xml_parser import XMLParserService

def test_parse_nfe_basic_structure():
    """Valida se o parser extrai corretamente os campos básicos e de impostos de uma NFe mockada."""
    parser = XMLParserService()
    
    xml_mock = b"""
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe Id="NFe35240200000000000000550010000000011000000010">
                <ide>
                    <nNF>1</nNF>
                    <serie>1</serie>
                    <dhEmi>2024-02-22T10:00:00-03:00</dhEmi>
                </ide>
                <emit>
                    <CNPJ>12345678000100</CNPJ>
                    <xNome>Empresa Teste LTDA</xNome>
                    <enderEmit><UF>SP</UF></enderEmit>
                </emit>
                <dest>
                    <CNPJ>98765432000199</CNPJ>
                    <xNome>Cliente Teste</xNome>
                    <enderDest><UF>RJ</UF></enderDest>
                </dest>
                <det nItem="1">
                    <prod>
                        <xProd>Produto Teste 01</xProd>
                        <NCM>12345678</NCM>
                        <CFOP>5102</CFOP>
                        <vProd>100.00</vProd>
                    </prod>
                    <imposto>
                        <vCBS>0.90</vCBS>
                        <vIBS>0.10</vIBS>
                        <PIS>
                            <PISAliq>
                                <vPIS>1.65</vPIS>
                            </PISAliq>
                        </PIS>
                        <COFINS>
                            <COFINSAliq>
                                <vCOFINS>7.60</vCOFINS>
                            </COFINSAliq>
                        </COFINS>
                    </imposto>
                </det>
                <total>
                    <ICMSTot>
                        <vNF>100.00</vNF>
                    </ICMSTot>
                    <vCBS>0.90</vCBS>
                    <vIBS>0.10</vIBS>
                </total>
            </infNFe>
        </NFe>
    </nfeProc>
    """
    
    result = parser.parse_nfe(xml_mock)
    
    assert result["chave_acesso"] == "35240200000000000000550010000000011000000010"
    assert result["numero"] == "1"
    assert result["valor_total"] == 100.00
    assert result["valor_cbs"] == 0.90
    assert result["valor_ibs"] == 0.10
    
    # Itens
    assert len(result["itens"]) == 1
    item = result["itens"][0]
    assert item["ncm"] == "12345678"
    assert item["v_cbs"] == 0.90
    assert item["v_ibs"] == 0.10
    assert item["v_pis"] == 1.65
    assert item["v_cofins"] == 7.60

def test_parse_nfe_malformed():
    """Verifica comportamento diante de XML inválido."""
    parser = XMLParserService()
    with pytest.raises(ValueError, match="XML corrompido"):
        parser.parse_nfe(b"not an xml")
