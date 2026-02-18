from app.core.supabase_client import SupabaseService

def check_companies():
    svc = SupabaseService()
    client = svc.get_client()
    
    # 1. Check all companies in the table
    res_all = client.table("empresas").select("*").execute()
    print(f"Total companies in DB: {len(res_all.data)}")
    for c in res_all.data:
        print(f" - Empresa: {c.get('razao_social')}, Tenant: {c.get('tenant_id')}, CNPJ: {c.get('cnpj')}")

    # 2. Check tenant existence
    tenant_id = "f81d4fae-7dec-11d0-a765-00a0c91e6bf6"
    res_tenant = client.table("tenants").select("*").eq("id", tenant_id).execute()
    print(f"Tenant '{tenant_id}' exists: {len(res_tenant.data) > 0}")

if __name__ == "__main__":
    check_companies()
