from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from typing import Dict, Any
from app_v5.services.xml_parser import XMLParserService
from app_v5.services.tax_validator import TaxValidatorService
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token
from app_v5.worker import process_nfe_xml_async
import base64
import logging

import os
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)

supabase_service = SupabaseService()
parser_service = XMLParserService()
validator_service = TaxValidatorService()

@router.post("/xml", summary="Upload e processamento de NF-e XML")
async def upload_xml(
    file: UploadFile = File(...),
    empresa_id: str = Form(None),
    token: str = Depends(get_current_token)
):
    """
    Recebe um arquivo XML, processa e valida conformidade tributária (CBS/IBS).
    """
    # 1. Validação de Tamanho (Anti-DoS)
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Limite de 5MB.")
    
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Arquivo deve ser um XML.")

    try:
        # Usamos o cliente do usuário para validar permissões (RLS)
        user_client = supabase_service.get_client_for_user(token)
        
        # Validar Token e Perfil via cliente do usuário
        user_res = user_client.auth.get_user()
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Sessão inválida ou expirada.")

        profile_res = user_client.table("profiles").select("tenant_id").eq("id", user_res.user.id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Usuário sem tenant vinculado.")

        # content já foi lido na linha 29 para validação de tamanho, reusando aqui.
        
        # 1. Verificação Síncrona de Duplicidade (Reduz carga na fila)
        nfe_data_quick = parser_service.parse_nfe(content)
        chave_acesso = nfe_data_quick.get("chave_acesso")
        
        check_existing = user_client.table("notas_fiscais").select("id").eq("chave_acesso", chave_acesso).eq("tenant_id", tenant_id).execute()
        if check_existing.data:
            return {
                "status": "already_processed",
                "nota_id": check_existing.data[0]['id'],
                "message": "Esta nota já foi enviada anteriormente."
            }

        # 2. Enviar para Fila Assíncrona (Celery)
        # Convertemos para base64 para o broker
        xml_b64 = base64.b64encode(content).decode('utf-8')
        
        task = process_nfe_xml_async.delay(xml_b64, tenant_id, empresa_id)
        
        logger.info(f"UPLOAD: Nota enfileirada (Job ID: {task.id}) para tenant {tenant_id}")

        return {
            "status": "enqueued",
            "job_id": task.id,
            "message": "Arquivo recebido. O processamento iniciou em segundo plano."
        }


    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        error_str = str(e)
        if "23505" in error_str or "duplicate key" in error_str:
            # Buscar nota existente para exibir ao usuário
            try:
                chave = nfe_data.get("chave_acesso")
                existing = client.table("notas_fiscais")\
                    .select("*, alertas_conformidade(*)")\
                    .eq("chave_acesso", chave)\
                    .eq("tenant_id", tenant_id)\
                    .single().execute()
                
                if existing.data:
                    nota = existing.data
                    # Só retornar se pertencer ao MESMO tenant (Garantia de isolamento)
                    if nota.get('tenant_id') == tenant_id:
                        return {
                            "file": file.filename,
                            "already_exists": True,
                            "parsed_data": nfe_data,
                            "validation": {
                                "status": nota["status"],
                                "validation_details": {
                                    "cbs_ok": nota["cbs_correto"],
                                    "ibs_ok": nota["ibs_correto"],
                                    "cbs_esperado": nota["valor_cbs"],
                                    "ibs_esperado": nota["valor_ibs"]
                                },
                                "alertas": nota["alertas_conformidade"]
                            },
                            "nota_id": nota["id"]
                        }
                    # Se for de outro tenant, fingir que é erro de inserção genérico
                    # ou apenas deixar passar para cair no raise 409 abaixo (mas, com a nova constraint,
                    # ele NÃO VAI cair no duplicate key se o tenant for diferente, vai INSERIR normal)
                    pass
            except Exception as inner_e:
                logger.warning(f"Falha ao recuperar nota existente: {inner_e}")
            
            raise HTTPException(
                status_code=409, 
                detail="Esta nota fiscal já foi processada. Tente carregar um novo arquivo."
            )

        error_details = traceback.format_exc()
        logger.error(f"Erro no upload: {error_details}")
        raise HTTPException(
            status_code=500, 
            detail={
                "message": "Erro interno ao processar nota.",
                "error": str(e)
            }
        )
