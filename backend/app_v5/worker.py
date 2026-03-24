from app_v5.services.xml_parser import XMLParserService
from app_v5.services.tax_validator import TaxValidatorService
from app_v5.core.supabase_client import SupabaseService
import logging
import base64
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

parser_service = XMLParserService()
validator_service = TaxValidatorService()
supabase_service = SupabaseService()


def process_nfe_xml_sync(xml_content_b64: str, tenant_id: str, empresa_id: str = None):
    """
    Processa uma nota fiscal de forma síncrona.
    - xml_content_b64: Conteúdo do XML em base64
    - tenant_id: ID do escritório
    - empresa_id: ID opcional da empresa vinculada
    """
    logger.info(f"WORKER: Iniciando processamento de nota para tenant {tenant_id}")

    try:
        xml_content = base64.b64decode(xml_content_b64)

        nfe_data = parser_service.parse_nfe(xml_content)

        validation_result = validator_service.validate_taxes(nfe_data, empresa_id=empresa_id)

        nota_id = supabase_service.insert_nfe_result(
            nfe_data,
            validation_result,
            tenant_id=tenant_id,
            empresa_id=empresa_id
        )

        logger.info(f"WORKER: Nota {nota_id} processada com sucesso.")
        return {"status": "success", "nota_id": nota_id, "chave": nfe_data.get("chave_acesso")}

    except Exception as e:
        logger.error(f"WORKER ERROR: Falha ao processar nota: {str(e)}")
        return {"status": "error", "message": str(e)}


async def sefaz_sync_task(empresa_id: str, tenant_id: str, triggered_by: str = "manual"):
    """
    Executa sincronização SEFAZ via BackgroundTasks do FastAPI.
    """
    from app_v5.services.sefaz_sync import SefazSyncService

    try:
        sync_service = SefazSyncService()
        result = await sync_service.sync_company_documents(empresa_id, tenant_id, triggered_by=triggered_by)
        return result
    except Exception as e:
        logger.error(f"SEFAZ WORKER: Crash fatal na task: {e}")
        return {"status": "error", "message": str(e)}
