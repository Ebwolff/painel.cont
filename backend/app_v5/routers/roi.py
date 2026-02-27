from fastapi import APIRouter, Depends, Response
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token, get_current_user
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()

@router.get("/strategic-intel", summary="Indicadores Estratégicos de BI")
async def get_strategic_intel(response: Response, empresa_id: str = None, user: dict = Depends(get_current_user)):
    # Prevent caching of sensitive BI data
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    """
    Gera indicadores de alto nível para o BI do contador.
    """
    try:
        user_id = user['id']
        token = user.get('access_token')
        
        # Obter cliente do usuário para respeitar RLS
        user_client = supabase_service.get_client_for_user(token)
        admin_client = supabase_service.get_service_client()
        
        # Verificar Role e Empresa
        profile_res = admin_client.table("profiles").select("role, empresa_id, tenant_id").eq("id", user_id).single().execute()
        profile = profile_res.data or {}
        role = profile.get('role')
        linked_company = profile.get('empresa_id')
        tenant_id = profile.get('tenant_id')
        
        if role == 'monitor':
            empresa_id = linked_company

        # 1. Buscar dados de notas
        query = user_client.table("notas_fiscais").select("status, valor_cbs, valor_ibs, created_at")
        if empresa_id:
            query = query.eq("empresa_id", empresa_id)
        
        res_total = query.execute()
        res_data = res_total.data or []
        
        total_notas = len(res_data)
        total_irregulares = len([n for n in res_data if n.get('status') == 'irregular'])

        # 2. Potencial de Glosa
        query_alertas = user_client.table("alertas_conformidade").select("diferenca").eq("resolvido", False)
        if empresa_id:
            query_alertas = query_alertas.eq("empresa_id", empresa_id)
        res_alertas_glosa = query_alertas.execute()
        glosa = sum(item.get('diferenca', 0) or 0 for item in (res_alertas_glosa.data or []))

        # 3. Evolução da Exposição
        meses_pt = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        evolucao_dict = {}
        
        for nota in res_data:
            if nota.get('status') != 'irregular': continue
            try:
                dt = datetime.fromisoformat(nota['created_at'].split('+')[0])
                mes_id = f"{dt.year}-{dt.month:02d}"
                valor = (nota.get('valor_cbs', 0) or 0) + (nota.get('valor_ibs', 0) or 0)
                evolucao_dict[mes_id] = evolucao_dict.get(mes_id, 0) + valor
            except: continue

        evolucao_final = []
        tendencia_exposicao = 0
        
        for i in range(5, -1, -1):
            d = datetime.now() - timedelta(days=i*30)
            mid = f"{d.year}-{d.month:02d}"
            label = meses_pt[d.month-1]
            val = evolucao_dict.get(mid, 0)
            evolucao_final.append({"mes": label, "valor": val})
            
            if i == 0: # Tendência baseada no mês anterior
                d_prev = datetime.now() - timedelta(days=30)
                mid_prev = f"{d_prev.year}-{d_prev.month:02d}"
                v_prev = evolucao_dict.get(mid_prev, 0)
                if v_prev > 0:
                    tendencia_exposicao = ((val - v_prev) / v_prev) * 100

        risco_dinamico = int((total_irregulares / total_notas * 100)) if total_notas > 0 else 0

        return {
            "indice_risco": risco_dinamico,
            "percentual_inconsistencia": (total_irregulares / total_notas * 100) if total_notas > 0 else 0,
            "potencial_glosa": glosa,
            "evolucao_exposicao": evolucao_final,
            "tendencia_exposicao": tendencia_exposicao
        }
    except Exception as e:
        logger.error(f"ROI: Erro Strategic Intel: {e}")
        return {"error": str(e)}


@router.get("/summary", summary="Relatório de ROI e Valor Realizado")
async def get_roi_summary(response: Response, empresa_id: str = None, user: dict = Depends(get_current_user)):
    # Prevent caching of sensitive ROI data
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    """
    Calcula o ROI consolidado.
    """
    try:
        token = user.get('access_token')
        user_client = supabase_service.get_client_for_user(token)
        admin_client = supabase_service.get_service_client()
        
        # Buscar perfil
        profile_res = admin_client.table("profiles").select("role, empresa_id, tenant_id").eq("id", user['id']).single().execute()
        profile = profile_res.data or {}
        role = profile.get('role')
        linked_company = profile.get('empresa_id')
            
        if role == 'monitor':
            empresa_id = linked_company
        
        # 1. Total de Créditos de Recuperação (Auditados via is_opportunity)
        query_alertas_opp = user_client.table("alertas_conformidade").select("diferenca").eq("is_opportunity", True).eq("resolvido", False)
        if empresa_id:
            query_alertas_opp = query_alertas_opp.eq("empresa_id", empresa_id)
        res_opp = query_alertas_opp.execute()
        total_recuperacao = sum(float(item.get('diferenca', 0) or 0) for item in (res_opp.data or []))

        # Preparar lista de CNPJs da empresa para filtrar Notas Emitidas
        query_empresas = user_client.table("empresas").select("cnpj")
        if empresa_id:
            query_empresas = query_empresas.eq("id", empresa_id)
        res_empresas = query_empresas.execute()
        cnpjs_empresa = [e.get('cnpj') for e in (res_empresas.data or []) if e.get('cnpj')]

        # 2. Total de Notas para Cálculo de Transição (Estimativa de Reforma)
        query_notas = user_client.table("notas_fiscais").select("valor_total, emitente_cnpj")
        if empresa_id:
            query_notas = query_notas.eq("empresa_id", empresa_id)
        
        res_notas = query_notas.execute()
        total_transicao = 0.0
        for item in (res_notas.data or []):
            if item.get('emitente_cnpj') in cnpjs_empresa:
                total_transicao += (float(item.get('valor_total', 0) or 0) * 0.01)
        
        # 2. Total de Alertas (Glosa)
        query_alertas = user_client.table("alertas_conformidade").select("diferenca").eq("resolvido", False)
        if empresa_id:
            query_alertas = query_alertas.eq("empresa_id", empresa_id)
        res_alertas = query_alertas.execute()
        total_glosa = sum(item.get('diferenca', 0) or 0 for item in (res_alertas.data or []))

        # 3. Alertas Resolvidos
        query_res = user_client.table("alertas_conformidade").select("diferenca").eq("resolvido", True)
        if empresa_id:
            query_res = query_res.eq("empresa_id", empresa_id)
        res_resolvidos = query_res.execute()
        alertas_resolvidos_count = len(res_resolvidos.data) if res_resolvidos.data else 0
        economia_realizada = sum(abs(item.get('diferenca', 0) or 0) for item in (res_resolvidos.data or []))
        
        return {
            "total_creditos_identificados": total_recuperacao + total_transicao,
            "creditos_recuperacao": total_recuperacao,
            "creditos_transicao": total_transicao,
            "alertas_resolvidos": alertas_resolvidos_count,
            "economia_estimada": economia_realizada,
            "potencial_glosa": total_glosa,
            "valor_mensal_plano": 499.00,
            "roi_ratio": (total_recuperacao + total_transicao + economia_realizada) / 499.00 if (total_recuperacao + total_transicao + economia_realizada) > 0 else 0
        }
    except Exception as e:
        logger.error(f"ROI: Erro summary: {e}")
        return {"error": str(e)}

