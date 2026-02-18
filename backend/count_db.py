import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def count_records():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    tables = ["alertas_conformidade", "notas_fiscais", "profiles", "tenants"]
    for table in tables:
        try:
            res = supabase.table(table).select("*", count="exact").limit(0).execute()
            print(f"Tabela {table}: {res.count} registros")
        except Exception as e:
            print(f"Erro ao contar {table}: {e}")

if __name__ == "__main__":
    count_records()
