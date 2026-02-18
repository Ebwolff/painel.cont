import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_policies():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Políticas de RLS ---")
    sql = """
    SELECT tablename, policyname, roles, cmd, qual
    FROM pg_policies
    WHERE schemaname = 'public'
    AND tablename IN ('empresas', 'notas_fiscais', 'alertas_conformidade');
    """
    # Usando RPC se disponível, ou apenas tentando inferir
    # Como não tenho RPC SQL fácil aqui, vou tentar um select na empresas com o token do carlos
    try:
        # Pega o token do carlos
        res_user = supabase.table("profiles").select("id").eq("nome", "carlos").execute()
        # Não consigo simular o token aqui sem logar.
        # Mas posso usar o service_role para ler a pg_policies se eu tiver permissão?
        # RPC costuma ser o jeito. Vou tentar um select simples na pg_policies via table()
        print("Tentando ler pg_policies...")
        res = supabase.rpc("get_policies", {}).execute() # Hipotético
        print(res.data)
    except:
        print("RPC 'get_policies' não encontrado. Vou tentar via Query SQL no terminal se possível ou apenas assumir e testar a correção.")

if __name__ == "__main__":
    check_policies()
