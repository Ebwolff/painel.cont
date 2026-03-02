import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def inspect_columns():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Fetch one record to see columns
    res = supabase.table("tenants").select("*").limit(1).execute()
    
    if res.data:
        print("Colunas na tabela 'tenants':")
        print(list(res.data[0].keys()))
    else:
        print("Tabela vazia ou erro ao buscar dados.")

if __name__ == "__main__":
    inspect_columns()
