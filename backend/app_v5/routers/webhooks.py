from fastapi import APIRouter, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from app_v5.core.supabase_client import SupabaseService
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()
supabase_service = SupabaseService()

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

class RpaResult(BaseModel):
    empresa_id: str
    chave: str
    status: str
    source: str = "RPA"
    xml_url: str | None = None
    error_details: str | None = None

@router.post("/rpa/nfe-status", summary="Recebe o resultado do robô RPA")
async def rpa_nfe_status(payload: RpaResult, auth_header: str = Security(api_key_header)):
    """
    Webhook chamado pelo rpa_worker quando o download da NF-e Emitida finaliza no Portal Nacional.
    """
    # Validação simples de segurança (deve bater com o config do rpa_worker)
    expected_secret = os.getenv("WEBHOOK_SECRET", "")
    if expected_secret and auth_header != f"Bearer {expected_secret}":
        raise HTTPException(status_code=401, detail="Webhook Secret inválido.")

    logger.info(f"WEBHOOK RPA RECEBIDO: {payload.chave} - Status: {payload.status}")

    try:
        admin_client = supabase_service.get_service_client()

        if payload.status == "COMPLETO" and payload.xml_url:
            # O RPA envia file://... se estivermos na mesma máquina/volume
            file_path = payload.xml_url.replace("file://", "")
            if not os.path.exists(file_path):
                logger.error(f"Arquivo XML não encontrado no disco: {file_path}")
                raise HTTPException(status_code=404, detail="XML físico não encontrado no volume compartilhado.")

            with open(file_path, "r", encoding="utf-8") as f:
                xml_content = f.read()

            # Salvar no Banco de Dados
            nota_data = {
                "chave": payload.chave,
                "empresa_id": payload.empresa_id,
                "tipo": "EMITIDA", # Forçando Emitida pois é o propósito desse robô RPA
                "xml_conteudo": xml_content,
                "status_sefaz": "Autorizado",
                "origem": "RPA",
            }
            
            # Upsert na tabela notas_fiscais
            res = admin_client.table("notas_fiscais").upsert(
                nota_data, on_conflict="chave, empresa_id"
            ).execute()

            logger.info(f"Nota {payload.chave} (RPA) salva com sucesso no banco de dados!")
            
            # Apagar arquivo temporário
            try:
                os.remove(file_path)
            except Exception as d_err:
                logger.warning(f"Não conseguiu apagar arquivo tmp: {d_err}")

        else:
            logger.warning(f"RPA Falhou para nota {payload.chave}. Erro: {payload.error_details}")

        return {"message": "Webhook processado com sucesso"}

    except Exception as e:
        logger.error(f"Erro processando Webhook RPA: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
