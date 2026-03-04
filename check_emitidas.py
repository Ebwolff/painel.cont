import os
import asyncio
from app_v5.core.supabase_client import SupabaseService

async def check():
    supabase = SupabaseService()
    admin_client = supabase.get_service_client()
    
    # CNPJ da DE VITO
    cnpj = "16968599000191"
    
    res_emitidas = admin_client.table("notas_fiscais").select("id", count="exact").eq("emitente_cnpj", cnpj).execute()
    print(f"Total emitidas encontradas no banco para o CNPJ {cnpj}: {res_emitidas.count}")
    
    res_recebidas = admin_client.table("notas_fiscais").select("id", count="exact").neq("emitente_cnpj", cnpj).execute()
    print(f"Total recebidas (onde emitente não é {cnpj}): {res_recebidas.count}")

if __name__ == "__main__":
    asyncio.run(check())
