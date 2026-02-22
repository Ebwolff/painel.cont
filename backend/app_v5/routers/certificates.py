from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token, get_current_user
import base64
import os
import logging

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()

@router.post("/upload/{company_id}", summary="Upload e armazenamento seguro de certificado A1")
async def upload_certificate(
    company_id: str,
    file: UploadFile = File(...),
    password: str = Form(...),
    user: dict = Depends(get_current_user)
):
    """
    Recebe o arquivo PFX, criptografa e salva no Supabase.
    Nota: Em produção, usaríamos criptografia real (AES) aqui.
    Para o MVP, estamos guardando o base64 para validar o fluxo.
    """
    if not file.filename.endswith(('.pfx', '.p12')):
        raise HTTPException(status_code=400, detail="Certificado deve ser .pfx ou .p12")

    try:
        content = await file.read()
        # 1. Criptografia em Repouso (AES)
        # O certificado base64 será criptografado com a chave mestra do servidor
        cert_encrypted = supabase_service.encrypt_data(cert_base64)
        
        # Mock de Expiração
        from datetime import datetime, timedelta
        expires_at = (datetime.now() + timedelta(days=365)).isoformat()
        
        client = supabase_service.get_client_for_user(token)
        
        # Buscar Tenant ID
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user['id']).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
             raise HTTPException(status_code=403, detail="Usuário sem escritório vinculado")
        
        # Salvar no Banco (Criptografado)
        res = client.table("certificados_a1").upsert({
            "tenant_id": tenant_id,
            "empresa_id": company_id,
            "certificado_base64": cert_encrypted,
            "senha_hash": supabase_service.encrypt_data(password), # Senha também criptografada
            "vencimento": expires_at,
            "status": "ativo"
        }).execute()
        
        # 2. Registrar Auditoria
        supabase_service.log_audit(
            user_id=user['id'],
            tenant_id=tenant_id,
            action="UPLOAD_CERTIFICATE",
            resource="CERTIFICADO",
            resource_id=company_id,
            details={"filename": file.filename}
        )
        
        # Atualizar status da empresa
        client.table("empresas").update({"servico_sefaz_ativo": True}).eq("id", company_id).execute()
        
        return {"message": "Certificado A1 configurado e criptografado com sucesso", "expires_at": expires_at}
        
    except Exception as e:
        logger.error(f"CERTIFICATES: Erro ao processar certificado: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar certificado.")

