from fastapi import APIRouter, Depends, HTTPException
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


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
        
        # 1. Buscar histórico (Base de comparação)
        res_hist = admin_client.table("notas_fiscais")\
            .select("id, valor_total, numero, created_at, emitente_cnpj, emitente_nome, destinatario_cnpj, destinatario_nome, status")\
            .eq("tenant_id", tenant_id)\
            .execute()
        
        notas = res_hist.data or []
        if not notas:
            return {"status": "insufficient_data", "anomalies": []}

        # Lógica 1: Desvio de Valor Médio
        valores = [float(n['valor_total'] or 0) for n in notas]
        media = sum(valores) / len(valores) if valores else 0
        anomalias_valor = [n for n in notas if float(n['valor_total'] or 0) > media * 3]
        
        results = []
        for anom in anomalias_valor:
            nota_id = anom.get('id')
            valor = float(anom['valor_total'] or 0)
            razao_multiplicacao = round(valor / media, 1) if media > 0 else 0
            
            # Buscar itens da nota para detalhamento
            itens_nota = []
            try:
                itens_res = admin_client.table("nfe_items")\
                    .select("n_item, ncm, cfop, cst, v_prod, descricao")\
                    .eq("nota_fiscal_id", nota_id)\
                    .execute()
                itens_nota = itens_res.data or []
            except Exception:
                pass

            results.append({
                "tipo": "valor_atípico",
                "detalhe": f"Nota {anom.get('numero', 'S/N')} com valor {valor:,.2f} está {razao_multiplicacao}x acima da média do período.",
                "severidade": "alta",
                "nota_numero": anom.get('numero', 'S/N'),
                "nota_id": nota_id,
                "valor": valor,
                "media_periodo": round(media, 2),
                "razao": razao_multiplicacao,
                "data_emissao": anom.get('created_at'),
                "emitente_cnpj": anom.get('emitente_cnpj'),
                "emitente_razao": anom.get('emitente_nome'),
                "destinatario_cnpj": anom.get('destinatario_cnpj'),
                "destinatario_razao": anom.get('destinatario_nome'),
                "status_nota": anom.get('status', 'pendente'),
                "itens": itens_nota,
                "problemas": [
                    {
                        "titulo": "Valor fora da curva estatística",
                        "descricao": f"O valor R$ {valor:,.2f} excede {razao_multiplicacao}x a média de R$ {media:,.2f} das {len(notas)} notas analisadas.",
                        "tipo_problema": "desvio_estatistico",
                        "impacto": "alto"
                    },
                    {
                        "titulo": "Risco de duplicidade ou erro de digitação",
                        "descricao": "Valores atípicos podem indicar nota duplicada, erro na digitação do valor, ou operação legítima que precisa ser justificada.",
                        "tipo_problema": "alerta_preventivo",
                        "impacto": "medio"
                    },
                    {
                        "titulo": "Verificação de base de cálculo recomendada",
                        "descricao": "Notas com valores elevados devem ter suas bases de cálculo (ICMS, PIS, COFINS) conferidas para evitar recolhimento incorreto.",
                        "tipo_problema": "recomendacao_fiscal",
                        "impacto": "medio"
                    }
                ]
            })

        return {
            "status": "success",
            "total_analisado": len(notas),
            "media_periodo": round(media, 2),
            "anomalies": results
        }
    except Exception as e:
        logger.error(f"ANOMALIES: Erro na análise: {e}")
        return {"status": "error", "message": str(e)}

