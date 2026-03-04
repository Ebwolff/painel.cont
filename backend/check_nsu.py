import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app_v5.core.supabase_client import SupabaseService

async def check():
    supa = SupabaseService().get_service_client()
    supa.table("certificados_a1").update({"ultimo_nsu": "000000000019224"}).eq("empresa_id", "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8").execute()
    print("NSU atualizado para 000000000019224")

if __name__ == "__main__":
    asyncio.run(check())
