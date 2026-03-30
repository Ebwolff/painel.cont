import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
import base64
import logging
logging.basicConfig(level=logging.INFO)

from app_v5.core.supabase_client import SupabaseService
from app_v5.services.sefaz_client import SefazClient

EMPRESA_ID = "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8"

def main():
    service = SupabaseService()
    client = service.get_service_client()
    
    cert_row = client.table("certificados_a1").select("certificado_enc, senha_enc, ambiente").eq("empresa_id", EMPRESA_ID).single().execute()
    pfx_bytes = base64.b64decode(service.decrypt_data(cert_row.data["certificado_enc"]))
    senha = service.decrypt_data(cert_row.data["senha_enc"])
    ambiente = cert_row.data.get("ambiente", "producao")
    
    nota = client.table("notas_fiscais").select("id, chave_acesso").eq("empresa_id", EMPRESA_ID).eq("is_resumo", True).eq("manifestado", False).limit(1).single().execute()
    chave = nota.data["chave_acesso"]
    
    emp = client.table("empresas").select("cnpj, uf").eq("id", EMPRESA_ID).single().execute()
    cnpj = emp.data["cnpj"]
    uf = emp.data.get("uf", "SP")
    
    sefaz = SefazClient(ambiente=ambiente)
    
    # We will monkey patch SefazClient._parse_evento_response or just let it run
    # Wait, the string replacement needs to happen before sending. We can do it in sefaz_client.py directly.
    pass

if __name__ == "__main__":
    main()
