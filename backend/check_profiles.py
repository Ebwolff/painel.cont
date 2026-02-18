import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_profiles():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Perfis Cadastrados ---")
    res = supabase.table("profiles").select("*").execute()
    print(json.dumps(res.data, indent=2))
    
    print("\n--- Alertas Cadastrados (Apenas Tenant ID) ---")
    res_alt = supabase.table("alertas_conformidade").select("id, tenant_id").execute()
    print(json.dumps(res_alt.data, indent=2))

if __name__ == "__main__":
    check_profiles()
