from fastapi import APIRouter, HTTPException, Depends
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token, get_current_user
import logging

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()

@router.get("/", summary="Lista empresas monitoradas")
def get_companies(user: dict = Depends(get_current_user)):
    """
    Lista empresas do contador logado (tenant).
    """
    try:
        user_id = user['id']
        
        # Buscar Tenant ID via Admin
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            return []
            
        # Buscar Empresas via Admin com filtro de Tenant
        res = admin_client.table("empresas").select("*").eq("tenant_id", tenant_id).execute()
        return res.data
    except Exception as e:
        logger.error(f"COMPANIES: Erro ao buscar lista: {e}")
        return []


from pydantic import BaseModel, Field
from typing import Optional

class CompanyCreate(BaseModel):
    razao_social: str = Field(..., min_length=2, max_length=150)
    cnpj: str = Field(..., min_length=14)
    regime_tributario: str = Field("lucro_real")

@router.post("/", summary="Cadastra nova empresa")
def create_company(company: CompanyCreate, user: dict = Depends(get_current_user)):
    try:
        client = supabase_service.get_client_for_user(user['access_token'])
        
        # Dados limpos e validados via Pydantic
        company_data = company.dict(exclude_none=True)
        cnpj = company_data["cnpj"].replace(".", "").replace("/", "").replace("-", "")
        company_data["cnpj"] = cnpj
        
        # Verificar se esse CNPJ já existe (CNPJ é único por empresa no Brasil)
        existing = client.table("empresas").select("id").eq("cnpj", cnpj).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Este CNPJ já está cadastrado no sistema.")

        # Garantir Tenant ID via Admin (Fail-safe)
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None

        if not tenant_id:
            raise HTTPException(status_code=400, detail="Usuário sem Tenant vinculado.")

        # 2. Validar limite de empresas do plano (se bloqueio estiver ativo)
        tenant_res = admin_client.table("tenants").select("limite_empresas, suspensao_limite").eq("id", tenant_id).single().execute()
        tenant_conf = tenant_res.data or {}
        limite = tenant_conf.get("limite_empresas", 5)
        bloquear = tenant_conf.get("suspensao_limite", False)
        
        if bloquear:
            usage_res = admin_client.table("empresas").select("id", count="exact").eq("tenant_id", tenant_id).execute()
            uso_atual = usage_res.count if usage_res.count is not None else 0
            
            if uso_atual >= limite:
                raise HTTPException(
                    status_code=403, 
                    detail=f"Limite de empresas atingido ({uso_atual}/{limite}). Faça upgrade ou entre em contato com o suporte para expandir sua carteira."
                )

        # Atribuir tenant_id de forma SEGURA no backend
        company_data["tenant_id"] = tenant_id

        # Inserção com payload controlado
        res = client.table("empresas").insert(company_data).execute()

        # Auditoria
        supabase_service.log_audit(
            user_id=user['id'],
            tenant_id=tenant_id,
            action="CREATE_COMPANY",
            resource="EMPRESA",
            resource_id=res.data[0]['id'] if res.data else None,
            details={"razao_social": company.razao_social}
        )
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"COMPANIES: Erro ao criar empresa: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar empresa.")


class CompanyUpdate(BaseModel):
    razao_social: Optional[str] = Field(None, min_length=2, max_length=150)
    cnpj: Optional[str] = Field(None, min_length=14)
    regime_tributario: Optional[str] = None

@router.put("/{company_id}", summary="Atualiza uma empresa")
def update_company(company_id: str, company: CompanyUpdate, user: dict = Depends(get_current_user)):
    try:
        # 1. Identificar tenant do usuário (Admin Client)
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user['id']).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Acesso negado.")

        user_client = supabase_service.get_client_for_user(user['access_token'])
        
        # Preparar payload apenas com campos fornecidos
        update_data = company.dict(exclude_unset=True, exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Nenhum dado fornecido para atualização.")
            
        if "cnpj" in update_data:
            cnpj = update_data["cnpj"].replace(".", "").replace("/", "").replace("-", "")
            update_data["cnpj"] = cnpj
            
            # Verificar se o novo CNPJ já existe em OUTRA empresa
            existing = user_client.table("empresas").select("id").eq("cnpj", cnpj).execute()
            if existing.data and existing.data[0]['id'] != company_id:
                raise HTTPException(status_code=400, detail="Este CNPJ já está cadastrado em outra empresa no sistema.")

        # Executar update com filtro explícito de tenant
        res = user_client.table("empresas")\
            .update(update_data)\
            .eq("id", company_id)\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Empresa não encontrada ou acesso negado.")

        # Auditoria
        supabase_service.log_audit(
            user_id=user['id'],
            tenant_id=tenant_id,
            action="UPDATE_COMPANY",
            resource="EMPRESA",
            resource_id=company_id,
            details=update_data
        )

        return res.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"COMPANIES: Erro ao atualizar empresa: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao atualizar empresa.")

@router.delete("/{company_id}", summary="Exclui uma empresa")
def delete_company(company_id: str, user: dict = Depends(get_current_user)):
    try:
        # 1. Identificar tenant do usuário (Admin Client)
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user['id']).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Acesso negado.")

        # 2. Executar delete com filtro explícito de tenant (User Client respeita RLS)
        user_client = supabase_service.get_client_for_user(user['access_token'])
        res = user_client.table("empresas")\
            .delete()\
            .eq("id", company_id)\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        if not res.data:
            raise HTTPException(status_code=404, detail="Empresa não encontrada ou acesso negado.")

        # Auditoria
        supabase_service.log_audit(
            user_id=user['id'],
            tenant_id=tenant_id,
            action="DELETE_COMPANY",
            resource="EMPRESA",
            resource_id=company_id
        )

        return {"message": "Empresa excluída com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"COMPANIES: Erro ao excluir empresa: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao excluir empresa.")

