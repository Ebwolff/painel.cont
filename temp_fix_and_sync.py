"""
FIX: Limpa os sync_jobs travados e reseta o certificado para permitir um novo sync.
DEPOIS: Dispara um sync real.
"""
import sys, os, asyncio
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app_v5.core.supabase_client import SupabaseService
from app_v5.services.sefaz_sync import SefazSyncService

EMPRESA_ID = "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8"  # DE VITO

def fix_stuck_state():
    service = SupabaseService()
    client = service.get_service_client()
    
    # 1. Limpar sync_jobs travados como "running"
    stuck = client.table("sync_jobs").update({
        "status": "cancelled",
        "error_message": "Limpeza automática de job travado"
    }).eq("status", "running").execute()
    print(f"Jobs travados limpos: {len(stuck.data or [])}")
    
    # 2. Garantir que o certificado está como "ativo" (não "sincronizando" nem "656")
    cert_fix = client.table("certificados_a1").update({
        "status": "ativo"
    }).eq("empresa_id", EMPRESA_ID).execute()
    print(f"Certificado resetado para 'ativo': {len(cert_fix.data or [])} registros")
    
    # 3. Buscar tenant_id
    emp = client.table("empresas").select("tenant_id").eq("id", EMPRESA_ID).single().execute()
    tenant_id = emp.data["tenant_id"]
    print(f"Tenant ID: {tenant_id}")
    return tenant_id

async def run_sync(tenant_id: str):
    sync_service = SefazSyncService()
    print("\n🚀 Disparando sync SEFAZ real para DE VITO...")
    result = await sync_service.sync_company_documents(EMPRESA_ID, tenant_id, triggered_by="fix_script")
    print(f"\n✅ Resultado do sync:")
    for k, v in result.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    tenant_id = fix_stuck_state()
    asyncio.run(run_sync(tenant_id))
