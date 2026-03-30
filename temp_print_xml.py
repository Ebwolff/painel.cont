"""
Debug: print the exact signed XML being sent to SEFAZ
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
import base64
from lxml import etree
from datetime import datetime, timezone

from app_v5.core.supabase_client import SupabaseService
from app_v5.services.xml_signer import XMLSigner
from app_v5.services.sefaz_endpoints import get_codigo_ibge_uf, gerar_id_lote

EMPRESA_ID = "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8"
NFE_NS = "http://www.portalfiscal.inf.br/nfe"

def main():
    service = SupabaseService()
    client = service.get_service_client()

    cert_row = client.table("certificados_a1").select("certificado_enc, senha_enc").eq("empresa_id", EMPRESA_ID).single().execute()
    pfx_bytes = base64.b64decode(service.decrypt_data(cert_row.data["certificado_enc"]))
    senha = service.decrypt_data(cert_row.data["senha_enc"])

    nota = client.table("notas_fiscais").select("chave_acesso").eq("empresa_id", EMPRESA_ID).eq("is_resumo", True).eq("manifestado", False).limit(1).single().execute()
    chave = nota.data["chave_acesso"]

    emp = client.table("empresas").select("cnpj, uf").eq("id", EMPRESA_ID).single().execute()
    cnpj = emp.data["cnpj"].replace(".", "").replace("/", "").replace("-", "")
    uf = emp.data.get("uf", "SP")

    tp_evento = "210210"
    c_orgao = get_codigo_ibge_uf(uf)
    n_seq = 1
    event_id = f"ID{tp_evento}{chave}{str(n_seq).zfill(2)}"
    dh_evento = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S-00:00")

    # Build evento XML
    evento = etree.Element("evento", versao="1.00", xmlns=NFE_NS)
    inf = etree.SubElement(evento, "infEvento", Id=event_id)
    etree.SubElement(inf, "cOrgao").text = c_orgao
    etree.SubElement(inf, "tpAmb").text = "1"
    etree.SubElement(inf, "CNPJ").text = cnpj
    etree.SubElement(inf, "chNFe").text = chave
    etree.SubElement(inf, "dhEvento").text = dh_evento
    etree.SubElement(inf, "tpEvento").text = tp_evento
    etree.SubElement(inf, "nSeqEvento").text = str(n_seq)
    etree.SubElement(inf, "verEvento").text = "1.00"
    det = etree.SubElement(inf, "detEvento", versao="1.00")
    etree.SubElement(det, "descEvento").text = "Ciencia da Operacao"

    # Sign
    signer = XMLSigner(pfx_bytes, senha)
    evento_assinado = signer.sign_event(evento, event_id)

    # Show signed evento
    print("=" * 60)
    print("EVENTO ASSINADO:")
    print("=" * 60)
    signed_xml = etree.tostring(evento_assinado, pretty_print=True, encoding="unicode")
    print(signed_xml)

    # Envelope
    env = etree.Element("envEvento", versao="1.00", xmlns=NFE_NS)
    etree.SubElement(env, "idLote").text = gerar_id_lote()
    env.append(evento_assinado)

    xml_str = etree.tostring(env, xml_declaration=False, encoding="unicode")
    print("\n" + "=" * 60)
    print("ENVELOPE COMPLETO:")
    print("=" * 60)
    print(xml_str[:3000])

if __name__ == "__main__":
    main()
