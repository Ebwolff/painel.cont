from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from app.services.sefaz_sync import SefazSyncService
from app.core.supabase_client import SupabaseService
from app.core.security import get_current_token

router = APIRouter()
sync_service = SefazSyncService()
supabase_service = SupabaseService()

@router.post("/trigger/{empresa_id}", summary="Dispara busca manual na SEFAZ")
async def trigger_sync(
    empresa_id: str, 
    background_tasks: BackgroundTasks,
    token: str = Depends(get_current_token)
):
    """
    Aciona a sincronização de documentos para uma empresa específica.
    """
    try:
        client = supabase_service.get_client_for_user(token)
        
        # Obter o tenant_id dinâmicamente do perfil do usuário logado
        res = client.rpc("get_my_tenant", {}).execute()
        tenant_id = res.data
        
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Escritório não identificado para este usuário.")
        
        background_tasks.add_task(sync_service.sync_company_documents, empresa_id, tenant_id)
        
        return {"message": "Sincronização iniciada em segundo plano."}
    except Exception as e:
        print(f"Erro ao disparar sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{empresa_id}")
async def get_sync_status(empresa_id: str):
    # TODO: Implementar log de jobs de sincronização no banco
    return {"empresa_id": empresa_id, "status": "idle", "last_sync": "2026-02-15T12:00:00"}
