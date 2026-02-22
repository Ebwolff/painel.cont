from app_v5.core.celery_app import celery_app
from app_v5.services.xml_parser import XMLParserService
from app_v5.services.tax_validator import TaxValidatorService
from app_v5.core.supabase_client import SupabaseService
import logging
import base64

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
        # Aqui o Sentry capturará automaticamente o erro se estiver configurado
        return {"status": "error", "message": str(e)}
