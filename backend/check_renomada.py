import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_tenant():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    res = supabase.table("tenants").select("*").ilike("nome", "%RENOMADA%").execute()
    if res.data:
        for t in res.data:
            print(f"Tenant: {t['nome']}")
            print(f"ID: {t['id']}")
            print(f"Plano: {t['plano']}")
            print(f"Limite: {t['limite_empresas']}")
            print(f"Suspensão: {t['suspensao_limite']}")
            print(f"Setup: {t['setup_pago']}")
            print("---")
    else:
        print("Tenant not found.")

if __name__ == "__main__":
    check_tenant()
