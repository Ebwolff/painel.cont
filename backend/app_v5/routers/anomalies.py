from fastapi import APIRouter, Depends, HTTPException
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user
from datetime import datetime, timedelta

router = APIRouter()
supabase_service = SupabaseService()

@router.get("/detect", summary="Detecção de Anomalias Fiscais")
def detect_anomalies(user: dict = Depends(get_current_user)):
    """
    Identifica comportamentos fora da curva no histórico do tenant.
    """
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # Obter tenant
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        # 1. Buscar histórico dos últimos 30 dias (Base de comparação)
        data_base = (datetime.now() - timedelta(days=30)).isoformat()
        res_hist = admin_client.table("notas_fiscais")\
            .select("valor_total, nNF, dhEmi")\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        notas = res_hist.data or []
        if not notas:
            return {"status": "insufficient_data", "anomalies": []}

        # Lógica Simples 1: Desvio de Valor Médio
        valores = [float(n['valor_total'] or 0) for n in notas]
        media = sum(valores) / len(valores)
        # Notas com valor > 3x a média são anomalias
        anomalias_valor = [n for n in notas if float(n['valor_total'] or 0) > media * 3]
        
        results = []
        for anom in anomalias_valor:
            results.append({
                "tipo": "valor_atípico",
                "detalhe": f"Nota {anom['nNF']} com valor {float(anom['valor_total']):,.2f} está 3x acima da média do período.",
                "severidade": "alta"
            })

        # Lógica Simples 2: Sequência de Notas (Gaps)
        # (Opcional - para futuro)

        return {
            "status": "success",
            "total_analisado": len(notas),
            "media_periodo": media,
            "anomalies": results
        }
    except Exception as e:
        print(f"Erro na análise de anomalias: {e}")
        return {"status": "error", "message": str(e)}
