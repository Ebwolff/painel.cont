import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

def debug_visibility():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- 1. Searching for user 'taless' ---")
    # Buscar na tabela profiles ou auth.users (via profiles é mais fácil com service role)
    res_profiles = supabase.table("profiles").select("*").ilike("nome", "%taless%").execute()
    
    user_tenant_id = None
    if res_profiles.data:
        for p in res_profiles.data:
            print(f"User Found: Name={p['nome']}, Email={p.get('email')}, ID={p['id']}, Role={p['role']}, Tenant={p['tenant_id']}")
            user_tenant_id = p['tenant_id']
    else:
        print("User 'taless' not found in profiles (checking by name).")

    print("\n--- 2. Listing All Companies ---")
    res_companies = supabase.table("empresas").select("*").execute()
    
    if res_companies.data:
        for c in res_companies.data:
            print(f"Company: ID={c['id']}, Razão Social={c['razao_social']}, Tenant={c['tenant_id']}, Status={c.get('status')}")
            
            if user_tenant_id and c['tenant_id'] == user_tenant_id:
                print(f"   [MATCH] Should be visible to user 'taless'!")
            elif user_tenant_id:
                print(f"   [MISMATCH] Different Tenant ID.")
    else:
        print("No companies found in database.")

if __name__ == "__main__":
    debug_visibility()
