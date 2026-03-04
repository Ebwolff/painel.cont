import asyncio
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

load_dotenv()

from app_v5.core.supabase_client import SupabaseService

async def get_cert_status():
    supa = SupabaseService().get_service_client()
    certs = supa.table("certificados_a1").select("empresa_id, ambiente, status, ultimo_sync, ultimo_nsu, updated_at").execute()
    
    print("--- STATUS DOS CERTIFICADOS NO BANCO ---")
    if not certs.data:
        print("Nenhum certificado encontrado na tabela.")
        return
        
    for idx, c in enumerate(certs.data):
        print(f"\nCertificado {idx + 1}:")
        print(f"  Empresa ID:  {c['empresa_id']}")
        print(f"  Status:      {c['status']}")
        print(f"  Ambiente:    {c['ambiente']}")
        print(f"  Ultimo Sync: {c['ultimo_sync']}")
        print(f"  Ultimo NSU:  {c['ultimo_nsu']}")
        print(f"  Atualizado:  {c['updated_at']}")

if __name__ == "__main__":
    asyncio.run(get_cert_status())
