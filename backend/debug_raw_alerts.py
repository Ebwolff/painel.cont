import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def debug_alerts():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Alertas Brutos (Service Role) ---")
    res = supabase.table("alertas_conformidade").select("*, notas_fiscais(*)").execute()
    print(json.dumps(res.data, indent=2))
    
    print("\n--- Notas Fiscais Brutas (Service Role) ---")
    res_nfe = supabase.table("notas_fiscais").select("*").execute()
    print(json.dumps(res_nfe.data, indent=2))

if __name__ == "__main__":
    debug_alerts()
