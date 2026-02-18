from app.core.supabase_client import SupabaseService
import os

def check_db():
    svc = SupabaseService()
    client = svc.get_client()
    
    tenant_id = "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
    
    # Check if tenant exists
    res = client.table("tenants").select("*").eq("id", tenant_id).execute()
    print(f"Tenant check: {res.data}")
    
    if not res.data:
        print("Creating seed tenant...")
        # Try to insert a seed tenant
        try:
            res = client.table("tenants").insert({
                "id": tenant_id,
                "nome": "Escritório Modelo END",
                "cnpj": "00.000.000/0001-00"
            }).execute()
            print(f"Tenant created: {res.data}")
        except Exception as e:
            print(f"Error creating tenant: {e}")

if __name__ == "__main__":
    check_db()
