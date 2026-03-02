import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_update():
    # We'll use the service role key to simulate a super admin if possible, 
    # but the API requires a bearer token. 
    # Actually, I can just use the supabase client directly to see if I can update it.
    from supabase import create_client, Client
    
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # 1. Get a tenant
    res = supabase.table("tenants").select("*").limit(1).execute()
    if not res.data:
        print("No tenants found.")
        return
    
    tenant = res.data[0]
    tid = tenant['id']
    old_limit = tenant.get('limite_empresas')
    new_limit = (old_limit or 0) + 1
    
    print(f"Updating tenant {tid} from limit {old_limit} to {new_limit}")
    
    update_res = supabase.table("tenants").update({
        "limite_empresas": new_limit,
        "plano": "pro"
    }).eq("id", tid).execute()
    
    if update_res.data:
        print("Update successful via direct client!")
        print(f"New data: {update_res.data[0]}")
    else:
        print("Update failed via direct client.")

    # Now verify if it persisted
    verify_res = supabase.table("tenants").select("*").eq("id", tid).single().execute()
    print(f"Persisted limit: {verify_res.data.get('limite_empresas')}")

if __name__ == "__main__":
    test_update()
