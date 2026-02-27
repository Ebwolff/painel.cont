from fastapi import APIRouter, Depends, HTTPException, Query
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user
from app_v5.services.simulation_service import SimulationService
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()
simulation_service = SimulationService()

# --- Models ---

class NFeItemMock(BaseModel):
    n_item: int = Field(..., description="Número do item")
    ncm: str = Field(..., description="Código NCM")
    cfop: str = Field(..., description="Código CFOP")
    cst: str = Field(..., description="Código CST")
    v_prod: float = Field(..., description="Valor do produto")
    v_cbs: float = 0.0
    v_ibs: float = 0.0
    v_icms: float = 0.0
    v_ipi: float = 0.0
    v_pis: float = 0.0
    v_cofins: float = 0.0

class NFeMockRequest(BaseModel):
    emitente_uf: str
    destinatario_uf: str
    itens: List[NFeItemMock]

# --- Endpoints ---

@router.get("/reform-impact", summary="Simulador de Impacto da Reforma Tributária")
def get_reform_impact(
    empresa_id: str = None, 
    custom_rate: Optional[float] = Query(None, description="Alíquota customizada para simulação interativa"),
    user: dict = Depends(get_current_user)
):
    """
    Calcula a projeção de impostos (Cenário Atual vs Reforma 2026)
    Agora suporta custom_rate para simulações interativas.
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
        
        if total_saidas == 0 and total_faturamento > 0:
            total_saidas = total_faturamento
        
        # 4. Cenários
        taxa_atual_est = 0.0925 
        custo_atual = total_faturamento * taxa_atual_est
        
        taxa_reforma_2026 = 0.01
        custo_reforma_2026 = total_faturamento * taxa_reforma_2026
        
        # Alíquota nominal pode ser customizada via parâmetro (Interatividade)
        taxa_reforma_full = custom_rate / 100 if custom_rate is not None else 0.275
        
        iva_debito = total_saidas * taxa_reforma_full
        iva_credito = total_entradas * taxa_reforma_full
        iva_liquido = max(0, iva_debito - iva_credito)
        
        margem_valor_agregado = total_saidas - total_entradas if total_saidas > 0 else 0
        aliquota_efetiva = (iva_liquido / total_saidas * 100) if total_saidas > 0 else 0

        return {
            "periodo_dias": 90,
            "total_faturamento": total_faturamento,
            "total_saidas": total_saidas,
            "total_entradas": total_entradas,
            "custom_rate_used": custom_rate is not None,
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
                    "nome": f"Reforma Plena (IVA {taxa_reforma_full*100:.1f}%)",
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


@router.post("/validate-nfe", summary="Simula conformidade de rascunho de NFe")
async def validate_nfe_mock(request: NFeMockRequest, user: dict = Depends(get_current_user)):
    """
    Valida os dados de uma nota fiscal antes da emissão.
    """
    try:
        # Converter modelos Pydantic para dicts para o SimulationService
        data = {
            "emitente_uf": request.emitente_uf,
            "destinatario_uf": request.destinatario_uf,
            "itens": [item.dict() for item in request.itens]
        }
        return simulation_service.simulate_nfe_compliance(data)
    except Exception as e:
        logger.error(f"SIMULATION: Erro na validação de rascunho: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assisted-calculation", summary="Gera pré-guia de apuração assistida")
async def get_assisted_calculation(empresa_id: str = None, user: dict = Depends(get_current_user)):
    """
    Consolida os valores de IBS/CBS das notas do último mês para apuração assistida.
    """
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Filtros de segurança
        profile_res = admin_client.table("profiles").select("tenant_id, role, empresa_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id")
        if profile_res.data.get("role") == "monitor":
            empresa_id = profile_res.data.get("empresa_id")

        # 2. Notas do mês atual
        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()
        query = admin_client.table("notas_fiscais").select("valor_total, valor_cbs, valor_ibs")\
            .eq("tenant_id", tenant_id)\
            .gte("created_at", inicio_mes)
            
        if empresa_id:
            query = query.eq("empresa_id", empresa_id)
            
        res = query.execute()
        return simulation_service.calculate_assisted_preview(res.data or [])
        
    except Exception as e:
        logger.error(f"SIMULATION: Erro na apuração assistida: {e}")
        raise HTTPException(status_code=500, detail="Erro ao gerar apuração assistida.")


