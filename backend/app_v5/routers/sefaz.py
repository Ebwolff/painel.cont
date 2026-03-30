from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Query
from app_v5.services.sefaz_sync import SefazSyncService
from app_v5.core.security import get_current_token
from app_v5.core.supabase_client import SupabaseService
import logging


logger = logging.getLogger(__name__)


router = APIRouter()
sync_service = SefazSyncService()
supabase_service = SupabaseService()


@router.post("/trigger/{empresa_id}", summary="Dispara busca na SEFAZ")
async def trigger_sync(
    empresa_id: str,
    token: str = Depends(get_current_token),
    background_tasks: BackgroundTasks = None,
):
    """
    Aciona a sincronização de documentos para uma empresa específica.
    Usa BackgroundTasks do FastAPI para execução assíncrona.
    """
    try:
        client = supabase_service.get_client_for_user(token)

        # Obter o tenant_id dinâmicamente do perfil do usuário logado
        res = client.rpc("get_my_tenant", {}).execute()
        tenant_id = res.data

        if not tenant_id:
            raise HTTPException(status_code=403, detail="Escritório não identificado para este usuário.")

        background_tasks.add_task(
            sync_service.sync_company_documents,
            empresa_id, tenant_id, triggered_by="manual"
        )
        return {
            "message": "Sincronização iniciada em segundo plano.",
            "mode": "background",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SEFAZ: Erro ao disparar sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-sync/{empresa_id}", summary="Executa sync síncrono para teste")
async def test_sync(
    empresa_id: str,
    token: str = Depends(get_current_token),
):
    """
    Executa a sincronização de forma síncrona (aguarda o fim) para validar o motor de regras.
    """
    try:
        client = supabase_service.get_client_for_user(token)

        # Obter tenant_id
        res = client.table("profiles").select("tenant_id").eq("id", client.auth.get_user().user.id).execute()
        if not res.data:
            raise HTTPException(status_code=403, detail="Perfil não encontrado.")

        tenant_id = res.data[0]["tenant_id"]

        # Executa de forma síncrona para retornar o resultado no Response
        result = await sync_service.sync_company_documents(empresa_id, tenant_id)

        return {
            "message": "Sincronização de teste concluída.",
            "result": result,
        }
    except Exception as e:
        logger.error(f"SEFAZ: Erro no test-sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{empresa_id}", summary="Status do último sync e histórico de jobs")
async def get_sync_status(
    empresa_id: str,
    token: str = Depends(get_current_token),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Retorna o status atual do certificado e os últimos sync_jobs para uma empresa.
    """
    try:
        admin_client = supabase_service.get_service_client()

        # Status do certificado
        cert_res = (
            admin_client.table("certificados_a1")
            .select("status, ultimo_sync, ultimo_nsu, ambiente, vencimento")
            .eq("empresa_id", empresa_id)
            .maybe_single()
            .execute()
        )

        # Últimos jobs
        jobs_res = (
            admin_client.table("sync_jobs")
            .select("id, status, started_at, finished_at, duration_ms, notas_processadas, notas_manifestadas, notas_completas, notas_com_erro, error_message, triggered_by")
            .eq("empresa_id", empresa_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return {
            "empresa_id": empresa_id,
            "certificado": cert_res.data if cert_res else None,
            "jobs": jobs_res.data if jobs_res else [],
        }
    except Exception as e:
        logger.error(f"SEFAZ: Erro ao buscar status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rpa/sincronizar/{empresa_id}", summary="Aciona robô RPA para buscar notas Emitidas")
async def rpa_sincronizar_emitidas(
    empresa_id: str,
    chave: str = Query(..., description="Chave de Acesso de 44 dígitos da NF-e Emitida"),
    token: str = Depends(get_current_token),
):
    """
    Envia um Job para a fila Redis do RPA (Python Playwright) baixar as notas Emitidas.
    A Vercel não ficará aguardando o processamento do robô.
    """
    import json
    import redis
    import os

    try:
        # Validar permissão da empresa
        client = supabase_service.get_client_for_user(token)
        res = client.rpc("get_my_tenant").execute()
        if not res.data:
            raise HTTPException(status_code=403, detail="Escritório não logado.")

        admin_client = supabase_service.get_service_client()
        cert_data = admin_client.table("certificados_a1").select("senha_hash").eq("empresa_id", empresa_id).maybe_single().execute()
        
        if not cert_data.data:
            raise HTTPException(status_code=400, detail="Empresa não possui Certificado A1 configurado.")

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.Redis.from_url(redis_url, decode_responses=True)

        job_payload = {
            "empresa_id": empresa_id,
            "chave": chave,
            "pfx_path": f"./certs/{empresa_id}.pfx",
            "pfx_password": cert_data.data["senha_hash"] 
        }

        r.rpush("nfe_download_queue", json.dumps(job_payload))

        return {
            "message": "Pedido enviado ao Robô RPA. A nota aparecerá na lista em alguns minutos.",
            "status": "QUEUED"
        }

    except Exception as e:
        logger.error(f"SEFAZ: Erro RPA despachante: {e}")
        raise HTTPException(status_code=500, detail=str(e))
