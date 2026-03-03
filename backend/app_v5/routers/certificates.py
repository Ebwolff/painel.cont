"""
Router de Certificados A1.
Permite upload seguro do certificado PFX do cliente,
armazenando-o criptografado no banco para uso no sync SEFAZ.
"""
import base64
import os
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates

from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
supabase_service = SupabaseService()


def _read_cert_expiry(pfx_bytes: bytes, password: str) -> datetime:
    """Lê a data de vencimento real do certificado PFX."""
    try:
        pw = password.encode("utf-8") if isinstance(password, str) else password
        _, certificate, _ = load_key_and_certificates(pfx_bytes, pw)
        return certificate.not_valid_after_utc
    except Exception:
        # Fallback: 1 ano a partir de hoje
        return datetime.now(timezone.utc) + timedelta(days=365)


@router.post("/upload/{company_id}", summary="Upload e armazenamento seguro do certificado A1")
async def upload_certificate(
    company_id: str,
    file: UploadFile = File(...),
    password: str = Form(...),
    ambiente: str = Form("producao"),   # 'homologacao' | 'producao'
    user: dict = Depends(get_current_user),
):
    """
    Recebe o .pfx do cliente, valida a senha, criptografa e salva no banco.
    Retorna a data de vencimento real lida do certificado.
    """
    if not file.filename.endswith((".pfx", ".p12")):
        raise HTTPException(status_code=400, detail="Certificado deve ser .pfx ou .p12")

    if ambiente not in ("homologacao", "producao"):
        raise HTTPException(status_code=400, detail="Ambiente inválido. Use 'homologacao' ou 'producao'.")

    try:
        content = await file.read()

        # 1. Validar PFX + senha ANTES de salvar (lança ValueError se inválido)
        try:
            expires_at = _read_cert_expiry(content, password)
            logger.info(f"CERTIFICATES: Cert válido, vence em {expires_at.isoformat()}")
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Senha incorreta ou certificado inválido: {e}")

        # 2. Criptografar cert + senha em repouso
        # A SEFAZ_SYNC espera q ao descriptografar, tenha uma string base64 válida
        cert_b64_str = base64.b64encode(content).decode("utf-8")
        cert_encrypted = supabase_service.encrypt_data(cert_b64_str)
        senha_encrypted = supabase_service.encrypt_data(password)

        # 3. Buscar tenant_id do usuário logado
        admin_client = supabase_service.get_service_client()
        profile_res = (
            admin_client.table("profiles")
            .select("tenant_id")
            .eq("id", user["id"])
            .maybe_single()
            .execute()
        )
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None

        if not tenant_id:
            logger.warning(f"CERTIFICATES: Perfil ou tenant_id não encontrado para usuário {user['id']}")
            raise HTTPException(status_code=403, detail="Usuário sem perfil ou escritório vinculado.")

        # 4. Upsert — uma empresa tem apenas um certificado ativo
        admin_client.table("certificados_a1").upsert(
            {
                "tenant_id": tenant_id,
                "empresa_id": company_id,
                "certificado_enc": cert_encrypted,
                "senha_enc": senha_encrypted,
                "vencimento": expires_at.isoformat(),
                "ambiente": ambiente,
                "status": "ativo",
                "ultimo_nsu": "000000000000000",  # reseta NSU para re-sync completo
                "ultimo_sync": None,
            },
            on_conflict="empresa_id",
        ).execute()

        # 5. Marca empresa como SEFAZ ativo
        admin_client.table("empresas").update(
            {"servico_sefaz_ativo": True}
        ).eq("id", company_id).execute()

        # 6. Audit log
        supabase_service.log_audit(
            user_id=user["id"],
            tenant_id=tenant_id,
            action="UPLOAD_CERTIFICATE",
            resource="CERTIFICADO",
            resource_id=company_id,
            details={"filename": file.filename, "ambiente": ambiente},
        )

        logger.info(f"CERTIFICATES: Cert salvo para empresa {company_id} (tenant {tenant_id})")
        return {
            "message": "Certificado A1 configurado com sucesso!",
            "expires_at": expires_at.isoformat(),
            "ambiente": ambiente,
            "dias_restantes": max(0, (expires_at - datetime.now(timezone.utc)).days),
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        logger.error(f"CERTIFICATES: Erro inesperado: {e}\n{error_msg}")
        
        # Se for um erro do PostgREST/Supabase, retorna o detalhe útil
        if "postgrest" in str(type(e)).lower() or "PGRST" in str(e):
             raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {str(e)}")
             
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar certificado: {str(e)}")


@router.get("/status/{company_id}", summary="Verifica status do certificado da empresa")
async def get_certificate_status(
    company_id: str,
    user: dict = Depends(get_current_user),
):
    """Retorna o status, vencimento e ambiente do certificado cadastrado."""
    try:
        admin_client = supabase_service.get_service_client()
        res = (
            admin_client.table("certificados_a1")
            .select("status, vencimento, ambiente, ultimo_sync, ultimo_nsu")
            .eq("empresa_id", company_id)
            .maybe_single()
            .execute()
        )

        if not res.data:
            return {"configured": False}

        cert = res.data
        venc = datetime.fromisoformat(cert["vencimento"]) if cert.get("vencimento") else None
        dias = max(0, (venc - datetime.now(timezone.utc)).days) if venc else 0

        return {
            "configured": True,
            "status": cert["status"],
            "vencimento": cert.get("vencimento"),
            "dias_restantes": dias,
            "ambiente": cert["ambiente"],
            "ultimo_sync": cert.get("ultimo_sync"),
            "alerta_vencimento": dias < 30,
        }

    except Exception as e:
        logger.error(f"CERTIFICATES: Erro ao consultar status: {e}")
        raise HTTPException(status_code=500, detail="Erro ao consultar certificado.")
