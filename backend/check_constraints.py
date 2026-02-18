import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_constraints():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # We can't easily query information_schema via API unless we use rpc.
    # But we can try to insert a duplicate with DIFFERENT tenant_id and see the error message.
    
    # 1. Fetch an existing note
    res = supabase.table("notas_fiscais").select("*").limit(1).execute()
    if not res.data:
        print("No notes found to test.")
        return

    existing_note = res.data[0]
    original_tenant = existing_note['tenant_id']
    chave = existing_note['chave_acesso']
    
    print(f"Existing Note: ID={existing_note['id']}, Tenant={original_tenant}, Chave={chave[:20]}...")
    
    # 2. Try to insert same chave with DIFFERENT tenant
    new_tenant = "6dbc5f1f-da52-4ea8-8105-611b243649a6" # Taless
    if original_tenant == new_tenant:
        new_tenant = "e34608e1-c7c1-4acf-afa9-63bae1521896" # Escritorio Modelo or other
        
    print(f"Attempting to insert duplicate chave for Tenant={new_tenant}...")
    
    payload = existing_note.copy()
    del payload['id']
    del payload['created_at']
    payload['tenant_id'] = new_tenant
    
    try:
        supabase.table("notas_fiscais").insert(payload).execute()
        print("SUCCESS! Constraint is NOT global (or composite).")
    except Exception as e:
        print(f"FAILED! Constraint IS global.\nError: {e}")

if __name__ == "__main__":
    check_constraints()
