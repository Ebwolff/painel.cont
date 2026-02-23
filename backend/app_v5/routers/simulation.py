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
    Agora com IVA Líquido: débito (vendas) - crédito (compras)
    Classifica via CFOP: 1/2/3xxx = entrada, 5/6/7xxx = saída
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

        # 2. Dados dos últimos 90 dias — notas fiscais
        data_limite = (datetime.now() - timedelta(days=90)).isoformat()
        
        query = admin_client.table("notas_fiscais").select("valor_total, valor_cbs, valor_ibs")\
            .eq("tenant_id", tenant_id)\
            .gte("created_at", data_limite)
            
        if empresa_id:
            query = query.eq("empresa_id", empresa_id)
            
        res = query.execute()
        notas = res.data or []
        
        total_faturamento = sum(float(n.get('valor_total', 0) or 0) for n in notas)
        
        # 3. Buscar nfe_items com CFOP para classificar entrada vs saída
        items_query = admin_client.table("nfe_items").select("cfop, v_prod")\
            .eq("tenant_id", tenant_id)\
            .gte("created_at", data_limite)
        
        if empresa_id:
            items_query = items_query.eq("tenant_id", tenant_id)  # já filtrado acima, mas mantém consistência
        
        items_res = items_query.execute()
        items = items_res.data or []
        
        total_saidas = 0.0
        total_entradas = 0.0
        
        for item in items:
            cfop = str(item.get('cfop', '') or '')
            v_prod = float(item.get('v_prod', 0) or 0)
            
            if cfop and len(cfop) >= 1:
                primeiro_digito = cfop[0]
                if primeiro_digito in ('5', '6', '7'):
                    total_saidas += v_prod
                elif primeiro_digito in ('1', '2', '3'):
                    total_entradas += v_prod
        
        # Fallback: se não houver itens classificados, usa total_faturamento como saída
        if total_saidas == 0 and total_faturamento > 0:
            total_saidas = total_faturamento
        
        # 4. Cenários
        # Cenário Atual (PIS 1.65% + COFINS 7.6% = 9.25%)
        taxa_atual_est = 0.0925 
        custo_atual = total_faturamento * taxa_atual_est
        
        # Cenário Reforma Transição (CBS 0.9% + IBS 0.1% = 1% em 2026)
        taxa_reforma_2026 = 0.01
        custo_reforma_2026 = total_faturamento * taxa_reforma_2026
        
        # Cenário Reforma Full com IVA Líquido
        taxa_reforma_full = 0.275
        iva_debito = total_saidas * taxa_reforma_full    # IVA sobre vendas
        iva_credito = total_entradas * taxa_reforma_full  # IVA sobre compras (crédito)
        iva_liquido = max(0, iva_debito - iva_credito)    # Empresa paga apenas a diferença
        
        # Margem efetiva para referência
        margem_valor_agregado = total_saidas - total_entradas if total_saidas > 0 else 0
        aliquota_efetiva = (iva_liquido / total_saidas * 100) if total_saidas > 0 else 0

        return {
            "periodo_dias": 90,
            "total_faturamento": total_faturamento,
            "total_saidas": total_saidas,
            "total_entradas": total_entradas,
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
                    "nome": "Reforma Plena (IVA Líquido)",
                    "aliquota_media": aliquota_efetiva,
                    "valor_estimado": iva_liquido,
                    "iva_debito": iva_debito,
                    "iva_credito": iva_credito,
                    "aliquota_nominal": taxa_reforma_full * 100,
                    "margem_valor_agregado": margem_valor_agregado
                }
            },
            "economia_transicao": custo_atual - custo_reforma_2026,
            "impacto_full": iva_liquido - custo_atual
        }

    except Exception as e:
        logger.error(f"SIMULATION: Erro no impacto da reforma: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar simulação estratégica.")

