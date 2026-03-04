import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app_v5.core.supabase_client import SupabaseService

async def check_db_tables():
    supa = SupabaseService().get_service_client()
    
    print("--- CONTAGEM DE DADOS ---")
    
    try:
        res = supa.table("notas_fiscais").select("id", count="exact").limit(1).execute()
        print(f"Total notas_fiscais (tabela principal): {res.count}")
    except Exception as e:
        print(f"Erro ao contar notas_fiscais: {e}")

    try:
        res = supa.table("nfe_items").select("id", count="exact").limit(1).execute()
        print(f"Total nfe_items (tabela principal): {res.count}")
    except Exception as e:
        print(f"Erro ao contar nfe_items: {e}")
        
    try:
        res = supa.table("certificados_a1").select("status, empresa_id, ultimo_nsu, ultimo_sync").execute()
        print("\n--- CERTIFICADOS ATUAIS ---")
        for c in res.data:
            print(f"Empresa: {c['empresa_id']} | Status: {c['status']} | NSU: {c['ultimo_nsu']} | Sync: {c['ultimo_sync']}")
    except Exception as e:
        print(f"Erro ao listar certificados: {e}")

if __name__ == "__main__":
    asyncio.run(check_db_tables())
