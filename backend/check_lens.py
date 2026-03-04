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
    res = supa.table("certificados_a1").select("*").eq("empresa_id", "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8").execute()
    c = res.data[0]
    enc_cert = c['certificado_enc']
    enc_pwd = c['senha_enc']
    print(f"LEN CERT: {len(enc_cert)}")
    print(f"LEN PWD: {len(enc_pwd)}")
    print(f"CERT START: {enc_cert[:20]}... END: {enc_cert[-20:]}")
    print(f"PWD: {enc_pwd}")

if __name__ == "__main__":
    asyncio.run(check())
