import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def inspect_nfe():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    nota_numero = "340992" # From the screenshot it was 340992... ah wait, the alert table says 1994487 in one screenshot... 
    # Let me search by the number in the alerts screenshot: 1994487
    
    print(f"--- Inspecionando Nota Fiscal 1994487 ---")
    res = supabase.table("notas_fiscais").select("id, numero, emitente_cnpj, destinatario_cnpj, tenant_id, empresa_id").eq("numero", "1994487").execute()
    
    if res.data:
        for n in res.data:
            print(f"ID: {n['id']}")
            print(f"Numero: {n['numero']}")
            print(f"Emitente CNPJ: {n['emitente_cnpj']}")
            print(f"Destinatário CNPJ: {n['destinatario_cnpj']}")
            print(f"Tenant ID: {n['tenant_id']}")
            print(f"Empresa ID: {n['empresa_id']}")
            print("-" * 20)
    else:
        print("Nota não encontrada.")

if __name__ == "__main__":
    inspect_nfe()
