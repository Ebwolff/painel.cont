from app_v5.core.celery_app import celery_app
from app_v5.services.xml_parser import XMLParserService
from app_v5.services.tax_validator import TaxValidatorService
from app_v5.core.supabase_client import SupabaseService
import logging
import base64
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Instâncias dos serviços (serão inicializadas no worker)
# Nota: SupabaseService usará a Service Key configurada nas env vars para o worker.
parser_service = XMLParserService()
validator_service = TaxValidatorService()
supabase_service = SupabaseService()

@celery_app.task(name="process_nfe_xml_async")
def process_nfe_xml_async(xml_content_b64: str, tenant_id: str, empresa_id: str = None):
    """
    Task assíncrona para processar uma nota fiscal.
    - xml_content_b64: Conteúdo do XML em base64 (para evitar problemas de serialização JSON)
    - tenant_id: ID do escritório
    - empresa_id: ID opcional da empresa vinculada
    """
    logger.info(f"WORKER: Iniciando processamento de nota para tenant {tenant_id}")
    
    try:
        # 1. Decodificar XML
        xml_content = base64.b64decode(xml_content_b64)
        
        # 2. Parse
        nfe_data = parser_service.parse_nfe(xml_content)
        
        # 3. Validação Tributária
        validation_result = validator_service.validate_taxes(nfe_data, empresa_id=empresa_id)
        
        # 4. Persistência (Supabase)
        # O worker sempre usa o service_client interno do SupabaseService
        nota_id = supabase_service.insert_nfe_result(
            nfe_data, 
            validation_result, 
            tenant_id=tenant_id, 
            empresa_id=empresa_id
        )
        
        logger.info(f"WORKER: Nota {nota_id} processada com sucesso via fila.")
        return {"status": "success", "nota_id": nota_id, "chave": nfe_data.get("chave_acesso")}

    except Exception as e:
        logger.error(f"WORKER ERROR: Falha ao processar nota: {str(e)}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="sefaz_sync_task", bind=True, max_retries=0, time_limit=600)
def sefaz_sync_task(self, empresa_id: str, tenant_id: str, triggered_by: str = "manual"):
    """
    Task Celery para sincronização SEFAZ com rastreamento via sync_jobs.
    Cria um registro de job, executa o sync, e atualiza o resultado.
    """
    from app_v5.services.sefaz_sync import SefazSyncService

    admin_client = supabase_service.get_service_client()
    job_id = None
    start_time = datetime.now(timezone.utc)

    try:
        # 1. Criar registro do job
        job_res = admin_client.table("sync_jobs").insert({
            "tenant_id": tenant_id,
            "empresa_id": empresa_id,
            "status": "running",
            "triggered_by": triggered_by,
            "started_at": start_time.isoformat(),
        }).execute()

        if job_res.data:
            job_id = job_res.data[0]["id"]
            logger.info(f"SEFAZ WORKER: Job {job_id} criado para empresa {empresa_id}")

    except Exception as e:
        logger.warning(f"SEFAZ WORKER: Falha ao criar sync_job: {e}")

    # 2. Executar sync
    try:
        sync_service = SefazSyncService()
        result = asyncio.run(sync_service.sync_company_documents(empresa_id, tenant_id))

        # 3. Atualizar job com resultado
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        if job_id:
            admin_client.table("sync_jobs").update({
                "status": result.get("status", "success"),
                "finished_at": end_time.isoformat(),
                "duration_ms": duration_ms,
                "notas_processadas": result.get("notas_processadas", 0),
                "notas_manifestadas": result.get("notas_manifestadas", 0),
                "notas_completas": result.get("notas_completas", 0),
                "notas_com_erro": result.get("notas_com_erro", 0),
                "novo_nsu": result.get("novo_nsu"),
                "error_message": result.get("message") if result.get("status") == "error" else None,
            }).eq("id", job_id).execute()

        logger.info(f"SEFAZ WORKER: Job {job_id} concluído em {duration_ms}ms — {result.get('status')}")
        return {"job_id": job_id, **result}

    except Exception as e:
        end_time = datetime.now(timezone.utc)
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        error_msg = str(e)[:500]

        if job_id:
            try:
                admin_client.table("sync_jobs").update({
                    "status": "error",
                    "finished_at": end_time.isoformat(),
                    "duration_ms": duration_ms,
                    "error_message": error_msg,
                }).eq("id", job_id).execute()
            except Exception:
                pass

        logger.error(f"SEFAZ WORKER: Job {job_id} falhou: {error_msg}")
        return {"job_id": job_id, "status": "error", "message": error_msg}

