from fastapi import APIRouter, Depends, HTTPException
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()

@router.get("/reform-impact", summary="Simulador de Impacto da Reforma Tributária")
def get_reform_impact(empresa_id: str = None, user: dict = Depends(get_current_user)):
    """
    Calcula a projeção de impostos (Cenário Atual vs Reforma 2026)
    Baseia-se nos últimos 90 dias de faturamento para uma amostragem robusta.
    """
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Obter perfil e tenant
        profile_res = admin_client.table("profiles").select("role, empresa_id, tenant_id").eq("id", user_id).single().execute()
        profile = profile_res.data or {}
        tenant_id = profile.get('tenant_id')
        role = profile.get('role')
        
        if role == 'monitor':
            empresa_id = profile.get('empresa_id')

        # 2. Dados dos últimos 90 dias
        data_limite = (datetime.now() - timedelta(days=90)).isoformat()
        
        query = admin_client.table("notas_fiscais").select("valor_total, valor_cbs, valor_ibs")\
            .eq("tenant_id", tenant_id)\
            .gte("created_at", data_limite)
            
        if empresa_id:
            query = query.eq("empresa_id", empresa_id)
            
        res = query.execute()
        notas = res.data or []
        
        total_faturamento = sum(float(n.get('valor_total', 0) or 0) for n in notas)
        
        # 3. Cenários
        # Cenário Atual (Estimado: PIS 1.65%, COFINS 7.6% = 9.25% total se não houver dados precisos)
        # Muitos clientes não destacam PIS/COFINS no XML (só no SPED), então usamos uma média de mercado para o simulador.
        taxa_atual_est = 0.0925 
        custo_atual = total_faturamento * taxa_atual_est
        
        # Cenário Reforma (CBS 0.9% + IBS 0.1% = 1% no período de transição 2026)
        taxa_reforma_2026 = 0.01
        custo_reforma_2026 = total_faturamento * taxa_reforma_2026
        
        # Cenário Reforma Full (Estimativa de 27.5% após transição)
        taxa_reforma_full = 0.275
        custo_reforma_full = total_faturamento * taxa_reforma_full

        return {
            "periodo_dias": 90,
            "total_faturamento": total_faturamento,
            "cenarios": {
                "atual": {
                    "nome": "Sistema Atual (PIS/COFINS)",
                    "aliquota_media": taxa_atual_est * 100,
                    "valor_estimado": custo_atual
                },
                "transicao_2026": {
                    "nome": "Transição 2026 (CBS/IBS)",
                    "aliquota_media": taxa_reforma_2026 * 100,
                    "valor_estimado": custo_reforma_2026
                },
                "reforma_full": {
                    "nome": "Reforma Plena (Estimativa)",
                    "aliquota_media": taxa_reforma_full * 100,
                    "valor_estimado": custo_reforma_full
                }
            },
            "economia_transicao": custo_atual - custo_reforma_2026,
            "impacto_full": custo_reforma_full - custo_atual
        }

    except Exception as e:
        logger.error(f"SIMULATION: Erro no impacto da reforma: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar simulação estratégica.")

