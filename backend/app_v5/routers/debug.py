from fastapi import APIRouter, Depends
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token
from datetime import datetime, timedelta

router = APIRouter()
supabase_service = SupabaseService()

@router.get("/debug", summary="Diagnóstico de Visibilidade")
async def debug_visibility(token: str = Depends(get_current_token)):
    diagnostics = {}
    try:
        # 1. Cliente
        client = supabase_service.get_client_for_user(token)
        diagnostics["client_status"] = "ok"
        
        # 2. Usuário Auth
        user = client.auth.get_user(token)
        diagnostics["user_id"] = user.user.id
        diagnostics["email"] = user.user.email
        
        # 3. Perfil
        profile_res = client.table("profiles").select("*").eq("id", user.user.id).single().execute()
        diagnostics["profile_data"] = profile_res.data
        
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        # 4. Contagem de Notas (Bruto vs RLS)
        res_rls = client.table("notas_fiscais").select("id", count="exact").execute()
        diagnostics["notas_visiveis_pelo_rls"] = res_rls.count
        
        # 5. Verificação via Service Role (O que existe de fato)
        service_client = supabase_service.get_service_client()
        res_real = service_client.table("notas_fiscais").select("id", count="exact").eq("tenant_id", tenant_id).execute()
        diagnostics["notas_existentes_no_tenant"] = res_real.count
        
        # 6. Verificação de Alertas
        res_alerts = client.table("alertas_conformidade").select("id", count="exact").execute()
        diagnostics["alertas_visiveis_pelo_rls"] = res_alerts.count

        return diagnostics
    except Exception as e:
        diagnostics["error"] = str(e)
        return diagnostics
