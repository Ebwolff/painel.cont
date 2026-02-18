import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_value():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Checking 'destinatario_nome' for Note 1994487 ---")
    res = supabase.table("notas_fiscais").select("id, numero, destinatario_nome, empresa_id").eq("numero", "1994487").execute()
    
    if res.data:
        for n in res.data:
            print(f"ID: {n['id']}")
            print(f"Numero: {n['numero']}")
            print(f"Destinatário Nome: '{n['destinatario_nome']}'")
            print(f"Empresa ID: {n['empresa_id']}")
    else:
        print("Nota não encontrada.")

if __name__ == "__main__":
    check_value()
