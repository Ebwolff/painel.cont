import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def fix_company():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Taless Tenant
    target_tenant = "6dbc5f1f-da52-4ea8-8105-611b243649a6"
    
    # Target Company (aees) - ID obtained from debug log
    # But to be safe, let's search by name "aees" in case ID changed or I copied it wrong,
    # Actually I learned the ID from the logs: 026b3866-0091-435b-b44e-8cf6048bac23
    
    target_company_id = "026b3866-0091-435b-b44e-8cf6048bac23"

    print(f"Updating company {target_company_id} to tenant {target_tenant}...")
    
    try:
        res = supabase.table("empresas").update({"tenant_id": target_tenant}).eq("id", target_company_id).execute()
        if res.data:
            print("Success! Company updated:", res.data[0])
        else:
            print("No data returned. Check if ID exists.")
            
    except Exception as e:
        print(f"Error updating company: {e}")

if __name__ == "__main__":
    fix_company()
