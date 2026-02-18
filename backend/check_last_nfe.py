import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_last():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    tenant_id = "6dbc5f1f-da52-4ea8-8105-611b243649a6" # Taless
    
    print(f"--- Checking Last NFe for Tenant: {tenant_id} ---")
    res = supabase.table("notas_fiscais").select("*").eq("tenant_id", tenant_id).order("created_at", desc=True).limit(1).execute()
    
    if res.data:
        print(res.data[0])
    else:
        print("No notes found.")

if __name__ == "__main__":
    check_last()
