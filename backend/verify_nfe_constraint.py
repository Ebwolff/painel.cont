import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time

load_dotenv()

def verify_constraint():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Verifying NFe Constraint Fix ---")

    # 1. Get an existing NFe
    res = supabase.table("notas_fiscais").select("*").limit(1).execute()
    if not res.data:
        print("No NFe found to test with.")
        return

    original_note = res.data[0]
    chave = original_note['chave_acesso']
    original_tenant = original_note['tenant_id']
    
    print(f"Original Note: Chave={chave[:10]}... Tenant={original_tenant}")

    # 2. Prepare duplicate payload for DIFFERENT tenant
    # Using 'taless' tenant if original is different, or 'escritorio_modelo' otherwise
    taless_tenant = "6dbc5f1f-da52-4ea8-8105-611b243649a6"
    target_tenant = taless_tenant if original_tenant != taless_tenant else "e34608e1-c7c1-4acf-afa9-63bae1521896"
    
    print(f"Testing insertion for Target Tenant: {target_tenant}")

    new_note = original_note.copy()
    del new_note['id']
    del new_note['created_at']
    if 'processado_em' in new_note: del new_note['processado_em']
    
    new_note['tenant_id'] = target_tenant
    if new_note.get('numero'):
        try:
            new_note['numero'] = str(int(new_note['numero']) + 900000)
        except:
            pass # Keep original if conversion fails
    else:
        new_note['numero'] = "900000"
    
    try:
        # Attempt Insert
        res_insert = supabase.table("notas_fiscais").insert(new_note).execute()
        print("✅ SUCCESS! The database ACCEPTED the duplicate key for a different tenant.")
        print("This means the SQL was executed correctly.")
        
        # Cleanup (delete the test note)
        new_id = res_insert.data[0]['id']
        supabase.table("notas_fiscais").delete().eq("id", new_id).execute()
        print("Test data cleaned up.")
        
    except Exception as e:
        err_str = str(e)
        if "23505" in err_str or "duplicate key" in err_str:
            print("❌ FAILURE! The database REJECTED the duplicate key.")
            print("This means the SQL has NOT been executed yet (Unique Constraint is still Global).")
        else:
            print(f"⚠️ Unexpected Error: {e}")

if __name__ == "__main__":
    verify_constraint()
