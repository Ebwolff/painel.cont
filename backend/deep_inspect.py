import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def deep_inspect():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não definidos.")
        return

    supabase: Client = create_client(url, service_key)
    
    # 1. Tentar listar tabelas via query direta (usando o fato que service_role pode fazer quase tudo)
    sql = """
    SELECT table_name, table_schema, table_type 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name;
    """
    
    print("--- Tabelas no Schema Public ---")
    try:
        # Nota: supabase-py não tem método direto para SQL raw, mas podemos usar o client rest para chamar algo se tiver RPC
        # Caso contrário, vamos apenas tentar acessar uma por uma das que sabemos
        res = supabase.table("notas_fiscais").select("*").limit(1).execute()
        print(f"✅ notas_fiscais: Acessível via service_role. Dados: {len(res.data)} linhas")
    except Exception as e:
        print(f"❌ notas_fiscais: ERRO -> {str(e)}")

    try:
        res = supabase.table("profiles").select("count").limit(0).execute()
        print(f"✅ profiles: OK")
    except Exception as e:
        print(f"❌ profiles: ERRO -> {str(e)}")

    # 2. Verificar se o erro de cache persiste no service_role
    print("\n--- Teste de Cache PostgREST ---")
    try:
        # Se der erro aqui, é cache do servidor Supabase
        res = supabase.table("notas_fiscais").select("id").limit(1).execute()
        print("✅ Cache PostgREST: A tabela foi encontrada agora.")
    except Exception as e:
        if "Could not find" in str(e):
            print(f"🚨 ERRO DE CACHE PERSISTENTE: {str(e)}")
        else:
            print(f"Inconsistência: {str(e)}")

if __name__ == "__main__":
    deep_inspect()
