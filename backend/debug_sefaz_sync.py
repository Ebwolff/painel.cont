import asyncio
import os
import sys
from dotenv import load_dotenv

# Configura path para achar os modulos
sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

load_dotenv()

from app_v5.services.sefaz_sync import SefazSyncService
from app_v5.core.supabase_client import SupabaseService

async def debug_sefaz():
    print("--- INICIANDO TESTE SEFAZ SYNC ---")
    
    # 1. Pega uma empresa que tenha certificado com erro
    supa_service = SupabaseService()
    supa = supa_service.get_service_client()
    certs = supa.table("certificados_a1").select("*").eq("empresa_id", "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8").execute()
    
    if not certs.data:
        print("Certificado não encontrado no banco.")
        return
        
    cert = certs.data[0]
    empresa_id = cert["empresa_id"]
    tenant_id = cert["tenant_id"]
    
    print(f"Empresa ID com erro: {empresa_id}")
    print(f"Tenant ID: {tenant_id}")
    print(f"Ambiente configurado: {cert['ambiente']}")
    print(f"Ultimo NSU: {cert['ultimo_nsu']}")
    
    
    from app_v5.services.sefaz_sync import SefazSyncService
    sync = SefazSyncService()
    try:
        print("\nForçando status do certificado para 'ativo' para teste...")
        supa.table("certificados_a1").update({"status": "ativo"}).eq("empresa_id", empresa_id).execute()
        print("\nRodando pelo SefazSyncService...")
        resultado = await sync.sync_company_documents(empresa_id, tenant_id)
        
        print("\n--- RESULTADO DA SYNC ---")
        print(resultado)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {type(e).__name__} - {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_sefaz())
