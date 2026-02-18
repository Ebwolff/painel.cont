from app.core.supabase_client import SupabaseService

def fix_data():
    svc = SupabaseService()
    client = svc.get_client()
    
    tenant_id = "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
    
    print("Fixing data...")
    
    # 1. Ensure tenant exists
    try:
        client.table("tenants").upsert({
            "id": tenant_id,
            "nome": "Escritório Modelo END",
            "cnpj": "00.000.000/0001-00"
        }).execute()
        print("Tenant created/verified.")
    except Exception as e:
        print(f"Tenant upsert error (check RLS): {e}")

    # 2. Update orphan companies
    try:
        res = client.table("empresas").update({"tenant_id": tenant_id}).is_("tenant_id", "null").execute()
        print(f"Updated {len(res.data)} companies to correct tenant.")
    except Exception as e:
        print(f"Company update error: {e}")

if __name__ == "__main__":
    fix_data()
