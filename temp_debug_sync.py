import asyncio
import os
import sys

# Adicionar path do backend
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app_v5.services.sefaz_sync import SefazSyncService

async def main():
    empresa_id = "89078652-5a21-4f9e-beaf-3467652796e6"
    tenant_id = "e0b82f05-0453-4f96-b0ad-e2009facf195" 
    
    print(f"--- Iniciando Sync Direto para {empresa_id} ---")
    sync_service = SefazSyncService()
    try:
        result = await sync_service.sync_company_documents(empresa_id, tenant_id)
        print("RESULTADO:", result)
    except Exception as e:
        import traceback
        print("CRASH FATAL:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
