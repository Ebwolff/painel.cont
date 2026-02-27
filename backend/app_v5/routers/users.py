from fastapi import APIRouter, Depends, HTTPException, status, Response
from app_v5.core.security import get_current_user
from app_v5.core.supabase_client import SupabaseService
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/users", tags=["Users"])
supabase_service = SupabaseService()

class UserCreate(BaseModel):
    email: str
    password: str
    nome: str
    role: str = Field('contador', pattern="^(admin|contador|monitor)$")
    empresa_id: str = None # Optional, required if role is monitor

class UserUpdatePermissions(BaseModel):
    permissions: dict

class UserUpdate(BaseModel):
    nome: str = Field(..., min_length=2)
    role: str = Field(..., pattern="^(admin|contador|monitor)$")
    empresa_id: str = None

@router.get("/my-tenant", summary="Listar usuários do meu tenant")
async def list_my_tenant_users(response: Response, user = Depends(get_current_user)):
    # Prevent caching of sensitive user list data
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    # 1. Obter tenant_id do usuário atual
    # O get_current_user já retorna o usuário autenticado, mas precisamos do perfil para saber o tenant_id
    # Vamos assumir que get_current_user retorna o objeto User do Supabase Auth
    
    # Para operações administrativas (criar user), precisamos do Service Key ou garantir que o usuário tenha permissão 'admin'
    # Vamos verificar se o usuário é admin do tenant
    
    client = supabase_service.get_client_for_user(user['access_token']) # type: ignore
    
    # Busca perfil
    profile_res = client.table("profiles").select("*").eq("id", user['id']).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=403, detail="Perfil não encontrado.")
    
    profile = profile_res.data
    
    if profile['role'] not in ['admin', 'super_admin']:
        # Contadores talvez possam ver colegas? Por enquanto, vamos restringir a admins
        raise HTTPException(status_code=403, detail="Apenas administradores podem gerenciar usuários.")
    
    tenant_id = profile['tenant_id']
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Usuário não vinculado a um escritório.")

    # Lista usuários do mesmo tenant
    # Service Client necessário para listar outros usuários? 
    # RLS 'Users see own tenant' deve permitir ver perfis do mesmo tenant.
    # Vamos tentar com client autenticado primeiro.
    
    res = client.table("profiles").select("*").eq("tenant_id", tenant_id).execute()
    return res.data

@router.post("/my-tenant", summary="Criar usuário para meu tenant")
async def create_user_for_my_tenant(new_user: UserCreate, user = Depends(get_current_user)):
    # Access Token for permission check
    token = user['access_token']
    client = supabase_service.get_client_for_user(token)
    
    # 1. Verifica permissão (Admin do Tenant)
    profile_res = client.table("profiles").select("*").eq("id", user['id']).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=403, detail="Perfil não encontrado.")
    
    profile = profile_res.data
    if profile['role'] not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Sem permissão para criar usuários.")
        
    tenant_id = profile['tenant_id']
    
    # Validation: If role is monitor, empresa_id is required
    if new_user.role == 'monitor' and not new_user.empresa_id:
        raise HTTPException(status_code=400, detail="Para monitor, é necessário selecionar uma empresa.")
    
    # 2. Criar Usuário no Auth (Requer Service Key - Admin API)
    # Admin do Tenant não tem permissão direta no Auth do Supabase, então o Backend usa a Service Key
    admin_client = supabase_service.get_service_client()
    
    # Validação de Hierarquia: Apenas Super Admin pode criar outro Admin ou Super Admin
    # Contador Admin pode criar apenas Contadores e Monitores
    requested_role = new_user.role
    if profile['role'] == 'contador' and requested_role in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Você não tem permissão para atribuir este nível de acesso.")
    
    if requested_role == 'super_admin' and profile['role'] != 'super_admin':
        raise HTTPException(status_code=403, detail="Apenas Super Admins podem criar outros Super Admins.")

    auth_res = admin_client.auth.admin.create_user({
        "email": new_user.email,
        "password": new_user.password,
        "email_confirm": True,
        "user_metadata": {
            "full_name": new_user.nome
        }
    })
    
    if hasattr(auth_res, 'error') and auth_res.error:
         raise HTTPException(status_code=400, detail=str(auth_res.error))
          
    created_user_id = auth_res.user.id
    
    # 3. Atualizar Profile com Tenant ID e Role
    # O trigger on_auth_user_created cria o profile, mas sem tenant_id (ou null)
    # Precisamos forçar o vínculo com o tenant do criador
    
    update_data = {
        "tenant_id": tenant_id,
        "role": new_user.role,
        "nome": new_user.nome,
        "empresa_id": new_user.empresa_id
    }
    
    admin_client.table("profiles").update(update_data).eq("id", created_user_id).execute()
    
    # Auditoria
    supabase_service.log_audit(
        user_id=user['id'],
        tenant_id=tenant_id,
        action="CREATE_USER",
        resource="USER",
        resource_id=created_user_id,
        details={"email": new_user.email, "role": new_user.role}
    )
    
    return {"msg": "Usuário criado com sucesso", "id": created_user_id}

@router.put("/{user_id}/permissions", summary="Atualizar permissões (Tenant Admin)")
async def update_permissions(user_id: str, data: UserUpdatePermissions, user = Depends(get_current_user)):
    token = user['access_token']
    client = supabase_service.get_client_for_user(token)
    
    # 1. Verifica quem está pedindo (Admin do Tenant)
    requester_res = client.table("profiles").select("tenant_id, role").eq("id", user['id']).single().execute()
    requester = requester_res.data
    
    if requester['role'] not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Sem permissão.")
        
    # 2. Verifica se o alvo pertence ao mesmo tenant
    target_res = client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
    target = target_res.data
    
    if not target or target['tenant_id'] != requester['tenant_id']:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou de outro escritório.")
        
    # 3. Atualiza
    admin_client = supabase_service.get_service_client()
    admin_client.table("profiles").update({"permissions": data.permissions}).eq("id", user_id).execute()
    
    # Auditoria
    supabase_service.log_audit(
        user_id=user['id'],
        tenant_id=requester['tenant_id'],
        action="UPDATE_PERMISSIONS",
        resource="USER",
        resource_id=user_id
    )
    
    return {"msg": "Permissões atualizadas"}

@router.delete("/{user_id}", summary="Excluir usuário (Tenant Admin)")
async def delete_user(user_id: str, user = Depends(get_current_user)):
    token = user['access_token']
    client = supabase_service.get_client_for_user(token)
    
    # 1. Verifica quem está pedindo (Admin do Tenant)
    requester_res = client.table("profiles").select("tenant_id, role").eq("id", user['id']).single().execute()
    requester = requester_res.data
    
    if requester['role'] not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Sem permissão.")
        
    # 2. Verifica se o alvo pertence ao mesmo tenant
    target_res = client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
    target = target_res.data
    
    if not target or target['tenant_id'] != requester['tenant_id']:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou de outro escritório.")
    
    # Can't delete yourself
    if user_id == user['id']:
        raise HTTPException(status_code=400, detail="Você não pode se excluir.")
        
    # 3. Deleta do Auth (Cascata deve deletar profile, mas garantimos via service key)
    admin_client = supabase_service.get_service_client()
    res = admin_client.auth.admin.delete_user(user_id)
    
    # Opcional: Deletar profile explicitamente se a cascata não estiver configurada
    admin_client.table("profiles").delete().eq("id", user_id).execute()
    
    # Auditoria
    supabase_service.log_audit(
        user_id=user['id'],
        tenant_id=requester['tenant_id'],
        action="DELETE_USER",
        resource="USER",
        resource_id=user_id
    )
    
    return {"msg": "Usuário excluído"}

@router.put("/{user_id}", summary="Atualizar dados do usuário (Tenant Admin)")
async def update_user(user_id: str, data: UserUpdate, user = Depends(get_current_user)):
    token = user['access_token']
    client = supabase_service.get_client_for_user(token)
    
    # 1. Verifica permissão
    requester_res = client.table("profiles").select("tenant_id, role").eq("id", user['id']).single().execute()
    requester = requester_res.data
    if requester['role'] not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="Sem permissão.")
        
    # 2. Verifica alvo
    target_res = client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
    target = target_res.data
    if not target or target['tenant_id'] != requester['tenant_id']:
        raise HTTPException(status_code=404, detail="Usuário não encontrado ou de outro escritório.")
        
    # 3. Atualiza Profile
    admin_client = supabase_service.get_service_client()
    
    # Validação de Hierarquia na Atualização
    if requester['role'] != 'super_admin' and data.role == 'super_admin':
        raise HTTPException(status_code=403, detail="Operação não permitida: Você não pode promover usuários a Super Admin.")
    
    if requester['role'] == 'contador' and data.role == 'admin':
         raise HTTPException(status_code=403, detail="Operação não permitida: Contador não pode promover usuários a Admin.")

    admin_client.table("profiles").update({
        "nome": data.nome,
        "role": data.role,
        "empresa_id": data.empresa_id
    }).eq("id", user_id).execute()
    
    return {"msg": "Usuário atualizado"}
