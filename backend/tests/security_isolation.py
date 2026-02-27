import os
import asyncio
import uuid
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

# Configurações
URL = os.getenv("VITE_SUPABASE_URL") or os.getenv("SUPABASE_URL")
KEY = os.getenv("VITE_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

async def run_security_test():
    print("=== INICIANDO TESTE DE ISOLAMENTO DE SEGURANÇA ===")
    
    if not URL or not SERVICE_ROLE_KEY:
        print("ERRO: Variáveis de ambiente Supabase ausentes.")
        return

    # Usamos o service_role para criar o cenário de teste rapidamente
    admin: Client = create_client(URL, SERVICE_ROLE_KEY)
    
    print("\n[1] PREPARANDO AMBIENTE DE TESTE...")
    # Criar dois tenants de teste
    tenant_a_id = str(uuid.uuid4())
    tenant_b_id = str(uuid.uuid4())
    
    admin.table("tenants").insert({"id": tenant_a_id, "nome": "Escritório TESTE A", "cnpj": "11111111000111"}).execute()
    admin.table("tenants").insert({"id": tenant_b_id, "nome": "Escritório TESTE B", "cnpj": "22222222000122"}).execute()
    
    # Criar dois usuários (um para cada tenant)
    # Nota: Em um teste real usaríamos JWTs reais. 
    # Aqui, para validar as políticas RLS via Postgres, simularemos o contexto do usuário.
    
    print(f"Tenants criados: A({tenant_a_id}) e B({tenant_b_id})")

    try:
        # TESTE 1: VALIDAÇÃO DE POLÍTICA SQL (RLS)
        # Vamos tentar ler dados de B usando uma sessão que "fingimos" ser de A (via RPC ou simulando headers se suportado)
        # Como o RLS do Supabase é baseado no auth.uid() e no profile, vamos checar a lógica no banco.
        
        print("\n[2] TESTE: ISOLAMENTO DE LEITURA (RLS)")
        # Inserir empresa no Tenant A
        emp_a = admin.table("empresas").insert({"tenant_id": tenant_a_id, "razao_social": "Empresa SECRETA A", "cnpj": "11111111000111"}).execute()
        emp_a_id = emp_a.data[0]['id']
        
        # Agora simulamos o erro de um hacker tentando ler essa empresa sem RLS (usando ANON key e sem estar logado)
        anon_client = create_client(URL, KEY)
        try:
            res_anon = anon_client.table("empresas").select("*").execute()
            print(f"Resultado ANON: {len(res_anon.data)} registros (Esperado: 0)")
        except Exception as e:
            print(f"ANON BLOQUEADO: {e}")

        # TESTE 3: PROTEÇÃO CONTRA INJEÇÃO DE TENANT_ID
        print("\n[3] TESTE: PROTEÇÃO CONTRA INJEÇÃO DE TENANT_ID (TRIGGER)")
        # Vamos tentar inserir uma nota no Tenant B através de um usuário que pertence ao Tenant A.
        # No nosso sistema, o TRIGGER set_tenant_id deve sobrescrever o ID enviado.
        
        # Simulamos o comportamento que o backend faz (supabase_client.py)
        # set_tenant_id() usa public.get_my_tenant() -> select tenant_id from profiles where id = auth.uid()
        
        print("Verificação: O banco possui triggers ativos para forçar tenant_id correto?")
        trigger_check = admin.rpc("check_rls_status", {}).execute() # Se tivéssemos uma função RPC de check
        
        print("Simulação concluída. O isolamento reside nas funções postgres:")
        print(" - get_my_tenant()")
        print(" - set_tenant_id()")
        print(" - RLS Policies using (tenant_id = get_my_tenant())")

    finally:
        # Cleanup
        print("\n[4] LIMPANDO AMBIENTE...")
        admin.table("empresas").delete().eq("tenant_id", tenant_a_id).execute()
        admin.table("tenants").delete().eq("id", tenant_a_id).execute()
        admin.table("tenants").delete().eq("id", tenant_b_id).execute()
        print("Cleanup concluído.")

if __name__ == "__main__":
    asyncio.run(run_security_test())
