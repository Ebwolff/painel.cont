from fastapi import APIRouter, Depends, HTTPException, status
from app_v5.core.security import get_current_token
from app_v5.core.supabase_client import SupabaseService
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/admin", tags=["Admin"])
supabase_service = SupabaseService()

class TenantCreate(BaseModel):
    nome: str
    cnpj: str
    plano: str = 'starter'

from typing import Optional

class TenantUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    plano: Optional[str] = None
    limite_empresas: Optional[int] = None
    suspensao_limite: Optional[bool] = None
    setup_pago: Optional[bool] = None


# --- PRICING ENGINE (Modelo Incremental por CNPJ) ---
PRICING_TIERS = [
    {"label": "Individual", "min": 1, "max": 1,  "fixed": 97.0},
    {"label": "Starter",    "min": 2, "max": 10, "rate": 40.0, "base_cost": 97.0, "base_qty": 1},
    {"label": "Escritório", "min": 11,"max": 50, "rate": 20.0, "base_cost": 97.0 + 9 * 40.0, "base_qty": 10},
    {"label": "Enterprise", "min": 51,"max": None,"rate": 10.0, "base_cost": 97.0 + 9 * 40.0 + 40 * 20.0, "base_qty": 50},
]

def calculate_billing(cnpj_count: int) -> dict:
    if cnpj_count <= 0:
        return {"tier": "Sem CNPJs", "monthly_value": 0.0, "cnpj_count": 0}
    for tier in PRICING_TIERS:
        if tier["max"] is None or cnpj_count <= tier["max"]:
            if "fixed" in tier:
                value = tier["fixed"]
            else:
                extra = cnpj_count - tier["base_qty"]
                value = tier["base_cost"] + extra * tier["rate"]
            return {
                "tier": tier["label"],
                "monthly_value": round(value, 2),
                "cnpj_count": cnpj_count,
                "rate_per_cnpj": round(value / cnpj_count, 2),
            }
    return {"tier": "Enterprise", "monthly_value": 0.0, "cnpj_count": cnpj_count}

# Dependency to check if user is super_admin
async def verify_super_admin(token: str = Depends(get_current_token)):
    client = supabase_service.get_client_for_user(token)
    user = client.auth.get_user(token)
    
    if not user or not user.user:
         raise HTTPException(status_code=401, detail="Unauthorized")

    # Check profile role
    res = client.table("profiles").select("role").eq("id", user.user.id).single().execute()
    if not res.data or res.data.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Apenas Super Admins podem acessar este recurso.")
    
    return client

@router.get("/tenants", summary="Listar todos os tenants com dados de billing (Super Admin)")
async def list_tenants(client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    tenants_res = admin_client.table("tenants").select("*").execute()
    tenants = tenants_res.data or []
    
    # Contar empresas monitoradas por tenant (CNPJs na carteira)
    companies_res = admin_client.table("empresas").select("tenant_id").execute()
    companies_data = companies_res.data or []
    
    # Construir mapa de contagem: {tenant_id: count}
    cnpj_count_map: dict = {}
    for company in companies_data:
        tid = company.get("tenant_id")
        if tid:
            cnpj_count_map[tid] = cnpj_count_map.get(tid, 0) + 1
    
    # Enriquecer cada tenant com dados de billing
    for tenant in tenants:
        count = cnpj_count_map.get(tenant["id"], 0)
        tenant["billing"] = calculate_billing(count)
    
    return tenants

@router.post("/tenants", summary="Criar novo tenant (Super Admin)")
async def create_tenant(tenant: TenantCreate, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    # Check if CNPJ exists
    check = admin_client.table("tenants").select("id").eq("cnpj", tenant.cnpj).execute()
    if check.data:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")
        
    try:
        res = admin_client.table("tenants").insert(tenant.dict()).execute()
        if not res.data:
             raise HTTPException(status_code=500, detail="Erro ao criar tenant: Sem dados retornados.")
        
        # Auditoria (Super Admin ação não tem tenant_id do alvo, logamos como global)
        supabase_service.log_audit(
            user_id=None, # Super Admin context
            tenant_id=res.data[0]['id'],
            action="CREATE_TENANT",
            resource="TENANT",
            resource_id=res.data[0]['id'],
            details={"nome": tenant.nome}
        )
        return res.data[0]
    except Exception as e:
        logger.error(f"ADMIN: Erro ao criar tenant: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {str(e)}")


@router.put("/tenants/{tenant_id}", summary="Atualizar tenant (Super Admin)")
async def update_tenant(tenant_id: str, data: TenantUpdate, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    update_payload = data.dict(exclude_unset=True)
    
    res = admin_client.table("tenants").update(update_payload).eq("id", tenant_id).execute()
    
    if not res.data:
         raise HTTPException(status_code=404, detail="Tenant não encontrado.")
         
    # Auditoria da alteração de plano/configuração
    supabase_service.log_audit(
        user_id=None, # Super Admin context
        tenant_id=tenant_id,
        action="UPDATE_TENANT_PLAN",
        resource="TENANT",
        resource_id=tenant_id,
        details=data.dict()
    )
    return res.data[0]

@router.delete("/tenants/{tenant_id}", summary="Excluir tenant (Super Admin)")
async def delete_tenant(tenant_id: str, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    # Excluir tenant (RLS e FK cascades cuidam do resto se configurado, senão precisamos de cuidado)
    res = admin_client.table("tenants").delete().eq("id", tenant_id).execute()
    
    if not res.data:
         raise HTTPException(status_code=404, detail="Tenant não encontrado.")
         
    return {"status": "deleted"}

# --- USER MANAGEMENT ---

class UserCreate(BaseModel):
    email: str
    password: str
    nome: str
    tenant_id: str
    role: str = 'contador' # 'admin' | 'contador'

class UserUpdatePermissions(BaseModel):
    permissions: dict

class UserAdminUpdate(BaseModel):
    nome: str
    role: str
    tenant_id: str

class PlanRequestProcess(BaseModel):
    status: str # 'approved' | 'rejected'
    admin_notes: str = None

@router.get("/users/{tenant_id}", summary="Listar usuários de um tenant (Super Admin)")
async def list_users(tenant_id: str, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    # Fetch profiles linked to this tenant
    res = admin_client.table("profiles").select("*").eq("tenant_id", tenant_id).execute()
    return res.data

@router.post("/users", summary="Criar novo usuário para um tenant (Super Admin)")
async def create_user(user: UserCreate, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    # 1. Create Auth User
    auth_res = admin_client.auth.admin.create_user({
        "email": user.email,
        "password": user.password,
        "email_confirm": True
    })
    
    if hasattr(auth_res, 'error') and auth_res.error:
         raise HTTPException(status_code=400, detail=str(auth_res.error))
         
    new_user_id = auth_res.user.id
    
    # 2. Update Profile (Trigger might have created it, or we create/update it)
    # Usually handle_new_user trigger creates profile. We update it with tenant_id and role.
    # But wait, trigger might default tenant_id to null or something.
    # Let's update the profile explicitly.
    
    profile_update = {
        "tenant_id": user.tenant_id,
        "nome": user.nome,
        "role": user.role
    }
    
    # Force update profile
    admin_client.table("profiles").update(profile_update).eq("id", new_user_id).execute()
    
    return {"id": new_user_id, "email": user.email, "msg": "Usuário criado com sucesso"}

@router.put("/users/{user_id}/permissions", summary="Atualizar permissões do usuário")
async def update_user_permissions(user_id: str, data: UserUpdatePermissions, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    res = admin_client.table("profiles").update({"permissions": data.permissions}).eq("id", user_id).execute()
    return res.data

@router.delete("/users/{user_id}", summary="Excluir usuário (Super Admin)")
async def delete_user(user_id: str, token: str = Depends(get_current_token), client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    # Impedir auto-exclusão
    current_user = client.auth.get_user(token)
    if current_user and current_user.user.id == user_id:
        raise HTTPException(status_code=400, detail="Você não pode excluir seu próprio usuário.")
        
    # Delete from Auth
    res = admin_client.auth.admin.delete_user(user_id)
    
    # Force delete profile
    admin_client.table("profiles").delete().eq("id", user_id).execute()
    
    return {"msg": "Usuário excluído"}

@router.put("/users/{user_id}", summary="Atualizar usuário (Super Admin)")
async def update_user(user_id: str, data: UserAdminUpdate, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    admin_client.table("profiles").update({
        "nome": data.nome,
        "role": data.role,
        "tenant_id": data.tenant_id
    }).eq("id", user_id).execute()
    
    return {"msg": "Usuário atualizado"}

@router.get("/dashboard-stats", summary="Obter estatísticas do painel (Super Admin)")
async def get_dashboard_stats(client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    # 1. Total Tenants
    tenants_res = admin_client.table("tenants").select("id", count="exact").execute()
    total_tenants = tenants_res.count if tenants_res.count else 0
    
    # 2. Total Usuários
    users_res = admin_client.table("profiles").select("id", count="exact").execute()
    total_users = users_res.count if users_res.count else 0
    
    # 3. Total XMLs Processados
    xml_res = admin_client.table("notas_fiscais").select("id", count="exact").execute()
    total_xmls = xml_res.count if xml_res.count else 0
    
    # 4. Recent Tenants (Limit 5)
    recent_res = admin_client.table("tenants").select("*").order("created_at", desc=True).limit(5).execute()
    
    # 5. MRR Real — baseado em CNPJs monitorados por cada tenant (modelo incremental)
    all_tenants_res = admin_client.table("tenants").select("id").execute()
    all_tenant_ids = [t["id"] for t in (all_tenants_res.data or [])]
    
    companies_res = admin_client.table("empresas").select("tenant_id").execute()
    cnpj_count_map: dict = {}
    for company in (companies_res.data or []):
        tid = company.get("tenant_id")
        if tid:
            cnpj_count_map[tid] = cnpj_count_map.get(tid, 0) + 1
    
    mrr = sum(calculate_billing(cnpj_count_map.get(tid, 0))["monthly_value"] for tid in all_tenant_ids)
    total_cnpjs = sum(cnpj_count_map.values())
    
    return {
        "total_tenants": total_tenants,
        "active_users": total_users,
        "processed_xmls": total_xmls,
        "total_cnpjs_monitored": total_cnpjs,
        "recent_tenants": recent_res.data,
        "plan_stats": {
            "mrr": round(mrr, 2)
        }
    }

# --- PLAN REQUESTS MANAGEMENT ---

@router.get("/requests", summary="Listar solicitações de upgrade (Super Admin)")
async def list_plan_requests(status: str = 'pending', client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    res = admin_client.table("plan_requests")\
        .select("*, tenants(nome, cnpj)")\
        .eq("status", status)\
        .order("created_at", desc=True)\
        .execute()
    return res.data

@router.put("/requests/{request_id}/process", summary="Processar solicitação de upgrade")
async def process_plan_request(request_id: str, data: PlanRequestProcess, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    
    # 1. Buscar solicitação
    req_res = admin_client.table("plan_requests").select("*").eq("id", request_id).single().execute()
    if not req_res.data:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada.")
    
    request_data = req_res.data
    tenant_id = request_data['tenant_id']
    requested_plan = request_data['requested_plan']
    
    # 2. Atualizar status da solicitação
    update_data = {
        "status": data.status,
        "processed_at": datetime.now().isoformat(),
        "admin_notes": data.admin_notes
    }
    admin_client.table("plan_requests").update(update_data).eq("id", request_id).execute()
    
    # 3. Se aprovado, atualizar plano do tenant
    if data.status == 'approved':
        admin_client.table("tenants").update({"plano": requested_plan}).eq("id", tenant_id).execute()
        
    return {"status": "processed", "result": data.status}
