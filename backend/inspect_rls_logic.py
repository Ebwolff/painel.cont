import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def inspect_rls():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Nota: No Supabase, para ler tabelas do sistema como pg_policies, 
    # as vezes precisamos usar uma função RPC que tenha privilégios de superuser.
    # Mas vamos tentar ler via um SELECT direto se possível (raro em PostgREST puro).
    # Como alternativa, vamos tentar um hack: ler profiles com o token do usuário (se tivéssemos).
    
    # Plano B: Vamos criar um script SQL de "Force Fix" que garante as políticas básicas
    # e pedir para o usuário rodar. Se o contador aparece mas a lista não, 
    # 99% de chance é RLS na subquery do tenant_id.
    
    print("Verificando se profiles tem RLS habilitado...")
    # Não conseguimos ver metadados de RLS via API PostgREST facilmente sem RPC.
    
    # Mas podemos testar: criar um alerta vázio e ver se aparece? Não.
    
    # Vou sugerir um script de "Reseto de RLS" que é mais garantido.
    print("Sugestão: Resetar políticas de RLS para garantir visibilidade.")

if __name__ == "__main__":
    inspect_rls()
