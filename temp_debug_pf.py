import sys
from backend.app_v5.services.xml_parser import XMLParserService

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
                <CPF>12345678901</CPF>
                <xNome>Produtor Rural PF</xNome>
                <enderEmit><UF>SP</UF></enderEmit>
            </emit>
            <dest>
                <CPF>10987654321</CPF>
                <xNome>Cliente PF</xNome>
                <enderDest><UF>RJ</UF></enderDest>
            </dest>
            <det nItem="1">
                <prod>
                    <xProd>Produto Teste PF</xProd>
                    <NCM>12345678</NCM>
                    <CFOP>5102</CFOP>
                    <vProd>100.00</vProd>
                </prod>
                <imposto>
                    <vCBS>0.90</vCBS>
                    <vIBS>0.10</vIBS>
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

try:
    res = parser.parse_nfe(xml_mock)
    print("PARSE RESULT:")
    print(res)

    from backend.app_v5.worker import process_nfe_xml_sync
    import base64

    # We can't insert it into supabase since we don't know the exact tenant.
    # But we can try validate_taxes!
    from backend.app_v5.services.tax_validator import TaxValidatorService
    val = TaxValidatorService()
    validation = val.validate_taxes(res, empresa_id="test")
    print("VALIDATION RESULT:")
    print(validation)
    
except Exception as e:
    import traceback
    traceback.print_exc()

