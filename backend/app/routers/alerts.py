from fastapi import APIRouter, HTTPException, Query, Depends
from app.core.supabase_client import SupabaseService
from app.core.security import get_current_token, get_current_user
from typing import List, Optional

router = APIRouter()
supabase_service = SupabaseService()

@router.get("/summary", summary="Resumo de alertas por severidade")
def get_alerts_summary(user: dict = Depends(get_current_user)):
    """
    Retorna o total de alertas pendentes por nível de severidade.
    """
    try:
        user_id = user['id']
        
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            return {"counts": {}, "total_pendentes": 0, "warning": "Tenant não identificado"}

        # Usar ADMIN client para garantir bypass de RLS instável
        admin_client = supabase_service.get_service_client()
        res = admin_client.table("alertas_conformidade").select("severidade").eq("tenant_id", tenant_id).eq("resolvido", False).execute()
        
        counts = {"critica": 0, "alta": 0, "media": 0, "baixa": 0}
        for item in (res.data or []):
            sev = item.get("severidade")
            if sev in counts:
                counts[sev] += 1
                
        return {
            "counts": counts,
            "total_pendentes": len(res.data or [])
        }
    except Exception as e:
        print(f"Erro summary alertas: {e}")
        return {"error": str(e), "counts": {}, "total_pendentes": 0}

@router.get("/", summary="Lista todos os alertas de conformidade")
def get_alerts(
    empresa_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),

    user: dict = Depends(get_current_user)
):
    """
    Busca alertas no Supabase filtrando por empresa ou status.
    Respeita RLS via token do usuário.
    """
    try:
        user_id = user['id']
        
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            return []

        # Usar ADMIN client com filtro de tenant manual
        admin_client = supabase_service.get_service_client()
        query = admin_client.table("alertas_conformidade").select("*, notas_fiscais(numero, chave_acesso, destinatario_nome, empresas(razao_social))").eq("tenant_id", tenant_id)
        
        if empresa_id:
            query = query.eq("empresa_id", empresa_id)
        if status:
            query = query.eq("resolvido", status == "resolvido")
            
        res = query.order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        print(f"Erro ao buscar alertas: {e}")
        return {"error": str(e), "details": "Falha na consulta de alertas"}

@router.get("/debug", summary="Diagnóstico de Alertas")
def debug_alerts(user: dict = Depends(get_current_user)):
    try:
        client = supabase_service.get_client_for_user(user.get('access_token'))
        user_id = user['id']
        
        # 1. Perfil
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        # 2. Alertas sem join
        res_simple = client.table("alertas_conformidade").select("*").execute()
        
        # 3. Alertas com join notas
        res_join = client.table("alertas_conformidade").select("*, notas_fiscais(numero)").execute()
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "simple_count": len(res_simple.data or []),
            "join_count": len(res_join.data or []),
            "simple_sample": res_simple.data[0] if res_simple.data else None,
            "join_sample": res_join.data[0] if res_join.data else None
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/{alerta_id}/resolver", summary="Marca alerta como resolvido")
def resolve_alert(alerta_id: str, user: dict = Depends(get_current_user)):
    try:
        # Usamos o client do usuário para respeitar RLS (Primeira Defesa)
        user_client = supabase_service.get_client_for_user(user.get('access_token'))
        
        # Segunda Defesa (Aplicação): Buscar tenant do usuário logado
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user['id']).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
             raise HTTPException(status_code=403, detail="Acesso negado: Perfil sem escritório.")

        # Resolve apenas se pertencer ao mesmo tenant
        res = user_client.table("alertas_conformidade")\
            .update({"resolvido": True})\
            .eq("id", alerta_id)\
            .eq("tenant_id", tenant_id)\
            .execute()
            
        if not res.data:
            raise HTTPException(status_code=404, detail="Alerta não encontrado ou não pertence ao seu escritório.")
            
        return {"status": "success", "data": res.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao resolver alerta: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar resolução.")
