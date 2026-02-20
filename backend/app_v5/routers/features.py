from fastapi import APIRouter, Depends, HTTPException, Query
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user

router = APIRouter()
supabase_service = SupabaseService()

# Definição dos Tiers
TIER_FEATURES = {
    "starter": ["basic_monitor", "upload_manual"],
    "pro": ["basic_monitor", "upload_manual", "roi_summary", "advanced_alerts", "sefaz_sync"],
    "enterprise": ["basic_monitor", "upload_manual", "roi_summary", "advanced_alerts", "sefaz_sync", "tax_reform_simulator", "ai_anomaly_detection", "executive_reports"]
}

@router.get("/my-features", summary="Listar recursos disponíveis para o plano atual")
def get_user_features(user: dict = Depends(get_current_user)):
    """
    Retorna a lista de funcionalidades habilitadas para o tenant do usuário.
    """
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Obter tenant e seu plano
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
             return {"tier": "starter", "features": TIER_FEATURES["starter"]}
             
        tenant_res = admin_client.table("tenants").select("plano, limite_empresas").eq("id", tenant_id).single().execute()
        plan = tenant_res.data.get("plano", "starter") if tenant_res.data else "starter"
        limite = tenant_res.data.get("limite_empresas", 5) if tenant_res.data else 5
        
        # 2. Obter uso atual
        usage_res = admin_client.table("empresas").select("id", count="exact").eq("tenant_id", tenant_id).execute()
        uso_atual = usage_res.count if usage_res.count is not None else 0
        
        return {
            "tier": plan,
            "features": TIER_FEATURES.get(plan, TIER_FEATURES["starter"]),
            "usage": {
                "companies_limit": limite,
                "companies_count": uso_atual
            }
        }
    except Exception as e:
        print(f"Erro ao buscar features: {e}")
        return {"tier": "starter", "features": TIER_FEATURES["starter"]}

@router.post("/set-plan", summary="DEBUG: Alterar plano do tenant (Apenas para demonstração)")
def set_tenant_plan(plan: str = Query(...), user: dict = Depends(get_current_user)):
    """
    DEBUG: Altera o plano do tenant logado.
    Em um sistema real, isso seria disparado por um webhook de pagamento (Stripe/Hotmart).
    """
    if plan not in TIER_FEATURES:
        raise HTTPException(status_code=400, detail="Plano inválido")
        
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Obter tenant
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
            
        # 2. Atualizar plano
        admin_client.table("tenants").update({"plano": plan}).eq("id", tenant_id).execute()
        
        return {"status": "success", "new_plan": plan}
    except Exception as e:
        print(f"Erro ao trocar plano: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/request-upgrade", summary="Solicitar upgrade de plano")
def request_upgrade(plan: str = Query(...), user: dict = Depends(get_current_user)):
    """
    Registra uma solicitação de upgrade para ser processada pelo Super Admin.
    """
    if plan not in TIER_FEATURES:
        raise HTTPException(status_code=400, detail="Plano inválido")
        
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Obter tenant
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            raise HTTPException(status_code=404, detail="Tenant não encontrado")
            
        # 2. Criar solicitação
        res = admin_client.table("plan_requests").insert({
            "tenant_id": tenant_id,
            "requested_plan": plan,
            "status": "pending"
        }).execute()
        
        return {"status": "requested", "data": res.data[0] if res.data else None}
    except Exception as e:
        print(f"Erro ao solicitar upgrade: {e}")
        raise HTTPException(status_code=500, detail=str(e))
