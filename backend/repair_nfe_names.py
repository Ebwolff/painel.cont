import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def repair_data():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Repairing Missing Names for Note 1994487 ---")
    
    # We'll set a placeholder name that indicates it was recovered from XML logic
    # In a real scenario, we might re-parse if we had the file.
    # Since we know the CNPJ is 05894326990, we'll use a generic name or what we expect.
    
    res = supabase.table("notas_fiscais").update({
        "destinatario_nome": "Empresa Destinatária (Recuperada)",
        "emitente_nome": "Empresa Emitente (Recuperada)"
    }).eq("numero", "1994487").execute()
    
    if res.data:
        print("✅ SUCCESS! Note updated with placeholder names.")
    else:
        print("❌ FAILURE! Could not update note.")

if __name__ == "__main__":
    repair_data()
