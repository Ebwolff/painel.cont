import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def verify_tables():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não definidos.")
        return

    supabase: Client = create_client(url, service_key)
    
    tables = ["tenants", "profiles", "empresas", "notas_fiscais", "alertas_conformidade"]
    
    print("--- Verificação Interna de Tabelas ---")
    for table in tables:
        try:
            # Tenta um select simples limitado a 0 para checar existência
            res = supabase.table(table).select("*", count="exact").limit(0).execute()
            print(f"✅ Tabela '{table}': OK")
        except Exception as e:
            print(f"❌ Tabela '{table}': ERRO -> {str(e)}")

if __name__ == "__main__":
    verify_tables()
