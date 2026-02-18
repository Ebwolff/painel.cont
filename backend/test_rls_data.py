import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def test_rls_functions():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Carlos ID
    carlos_id = "78351bb6-0347-4fc5-99c0-8874720036c8"
    
    print(f"--- Diagnóstico de Funções e Vínculos (Carlos: {carlos_id}) ---")
    
    # 1. Verificar se a função get_my_tenant existe via RPC (simulando Carlos)
    # Nota: RPC costuma ignorar RLS se for SECURITY DEFINER
    try:
        # Precisamos de um token do Carlos para testar RPC como ele, 
        # mas como não temos, vamos ler a definição da função via SQL.
        sql = "SELECT routine_name, routine_definition FROM information_schema.routines WHERE routine_name = 'get_my_tenant'"
        # Infelizmente não temos console SQL direto aqui, mas posso tentar inferir.
        pass
    except: pass

    # 2. Verificar se as tabelas de apoio têm dados para o tenant do Carlos
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896"
    
    counts = {}
    for table in ["empresas", "notas_fiscais", "alertas_conformidade"]:
        res = supabase.table(table).select("id", count="exact").eq("tenant_id", tenant_id).execute()
        counts[table] = res.count
    
    print(f"Dados físicos para o Tenant {tenant_id}:")
    print(json.dumps(counts, indent=2))

    # 3. Se existem dados físicos mas o Carlos não vê, o problema é a regra 'tenant_id = get_my_tenant()'
    # ou 'tenant_id = (select tenant_id from profiles...)'
    
if __name__ == "__main__":
    test_rls_functions()
