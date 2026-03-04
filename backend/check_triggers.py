import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app_v5.core.supabase_client import SupabaseService

async def check_triggers():
    supa = SupabaseService().get_service_client()
    
    # Executar uma query SQL direta usando raw query no Supabase não é fácil pela API REST,
    # Mas podemos tentar com a função RPC se existir, 
    # ou usando postgres python client psycopg2 se eu tiver a string de conexao.
    # supabase_url = os.environ.get("SUPABASE_URL")
    # A DSN de conexão seria algo como postgresql://...
    pass

    print("Checking triggers using RPC if possible...")
    # Supabase REST nao suporta consultas nativas na information_schema.
    # Vamos listar apenas os dados brutos da tabela para ver o que tem nela.
    res = supa.table("certificados_a1").select("*").execute()
    for row in res.data:
        print(row)

if __name__ == "__main__":
    asyncio.run(check_triggers())
