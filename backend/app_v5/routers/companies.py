from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase_client import SupabaseService
from app.core.security import get_current_token, get_current_user

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
        print(f"Erro ao buscar empresas: {e}")
        return []

from pydantic import BaseModel, Field

class CompanyCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    cnpj: str = Field(..., pattern=r"^\d+$")
    razao_social: str = Field(None, max_length=150)
    email: str = Field(None)
    telefone: str = Field(None)

@router.post("/", summary="Cadastra nova empresa")
def create_company(company: CompanyCreate, user: dict = Depends(get_current_user)):
    try:
        client = supabase_service.get_client_for_user(user['access_token'])
        
        # Dados limpos e validados via Pydantic
        company_data = company.dict()
        cnpj = company_data["cnpj"]
        
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
            details={"nome": company.nome}
        )
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating company: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao salvar empresa.")

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
        print(f"Error deleting company: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao excluir empresa.")
