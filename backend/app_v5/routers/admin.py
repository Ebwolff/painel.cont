from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_token
from app.core.supabase_client import SupabaseService
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["Admin"])
supabase_service = SupabaseService()

class TenantCreate(BaseModel):
    nome: str
    cnpj: str
    plano: str = 'free'

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

@router.get("/tenants", summary="Listar todos os tenants (Super Admin)")
async def list_tenants(client = Depends(verify_super_admin)):
    # Super admin needs to see all tenants using SERVICE ROLE KEY usually, 
    # OR we rely on RLS policies that allow super_admin to see everything.
    # For now, let's use the authenticated client assuming RLS allows super_admin to select from tenants.
    # If RLS on 'tenants' table is "Users see own tenant", super_admin won't see others unless we change policy or use service key.
    
    # STRATEGY: Use Service Key for Admin Operations to bypass RLS limits designed for regular users.
    # verify_super_admin already confirmed the user is legit.
    
    admin_client = supabase_service.get_service_client() # Using service role client for admin ops
    
    res = admin_client.table("tenants").select("*").execute()
    return res.data

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
        raise HTTPException(status_code=500, detail=f"Erro no banco de dados: {str(e)}")

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
    
    # 2. Total Usuários (Todos os escritórios)
    users_res = admin_client.table("profiles").select("id", count="exact").execute()
    total_users = users_res.count if users_res.count else 0
    
    # 3. Total XMLs Processados (Global)
    xml_res = admin_client.table("notas_fiscais").select("id", count="exact").execute()
    total_xmls = xml_res.count if xml_res.count else 0
    
    # 4. Recent Tenants (Limit 5)
    recent_res = admin_client.table("tenants").select("*").order("created_at", desc=True).limit(5).execute()
    
    return {
        "total_tenants": total_tenants,
        "active_users": total_users,
        "processed_xmls": total_xmls,
        "recent_tenants": recent_res.data
    }
