from fastapi import APIRouter, Depends
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token, get_current_user
from typing import Dict, List
from datetime import datetime, timedelta

router = APIRouter()
supabase_service = SupabaseService()

@router.get("/strategic-intel", summary="Indicadores Estratégicos de BI")
def get_strategic_intel(empresa_id: str = None, user: dict = Depends(get_current_user)):
    """
    Gera indicadores de alto nível para o BI do contador:
    Respeita RLS. Se for Monitor, força o filtro pela empresa vinculada.
    """
    try:
        user_id = user['id']

        # Verificar Role e Empresa
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("role, empresa_id, tenant_id").eq("id", user_id).single().execute()
        profile = profile_res.data or {}
        role = profile.get('role')
        linked_company = profile.get('empresa_id')
        tenant_id = profile.get('tenant_id')
        
        print(f"DEBUG ROI INTEL: User={user_id}, Tenant={tenant_id}, Role={role}")
        
        # Se for Monitor, IGNORA o parametro empresa_id e usa o vinculado
        if role == 'monitor':
            if not linked_company:
                return {"indice_risco": 0, "percentual_inconsistencia": 0, "potencial_glosa": 0, "evolucao_exposicao": []}
            empresa_id = linked_company

        # Usar user_client para buscar dados respeitando RLS
        query = user_client.table("notas_fiscais").select("status, valor_cbs, valor_ibs, created_at")
        if empresa_id:
            query = query.eq("empresa_id", empresa_id)
        
        res_total = query.execute()
        
        total_notas = len(res_total.data) if res_total.data else 0
        notas_irregulares = [n for n in res_total.data if n.get('status') == 'irregular']
        total_irregulares = len(notas_irregulares)

        # 1. Potencial de Glosa (Soma das diferenças nos alertas pendentes)
        query_alertas = user_client.table("alertas_conformidade").select("diferenca").eq("resolvido", False)
        if empresa_id:
            query_alertas = query_alertas.eq("empresa_id", empresa_id)
        res_alertas_glosa = query_alertas.execute()
        glosa = sum(item.get('diferenca', 0) or 0 for item in (res_alertas_glosa.data or []))

        # Buscar risco score do tenant
        try:
            res_tenant = admin_client.table("tenants").select("risco_score").eq("id", tenant_id).execute()
            risco_base = res_tenant.data[0].get('risco_score', 45) if res_tenant.data else 45
        except Exception:
            risco_base = 45

        # 3. Evolução da Exposição (Últimos 6 meses)
        data_semestre = (datetime.now() - timedelta(days=180)).isoformat()
        # Reutilizar dados já buscados ou fazer nova query se precisar de mais histórico
        res_evolucao_data = res_total.data or [] # Já temos todas as notas (RLS cuida do tenant)

        meses_pt = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        evolucao_dict = {}
        
        for nota in res_evolucao_data:
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
            
            # Se for o mês atual e o anterior, calculamos a tendência
            if i == 0: # Atual
                v_atual = val
                d_prev = datetime.now() - timedelta(days=30)
                mid_prev = f"{d_prev.year}-{d_prev.month:02d}"
                v_prev = evolucao_dict.get(mid_prev, 0)
                if v_prev > 0:
                    tendencia_exposicao = ((v_atual - v_prev) / v_prev) * 100

        # 2. Índice de Risco (Dinâmico, baseado na taxa de inconsistência)
        # Padronizando com Dashboard: inconsistência = risco
        risco_dinamico = int((total_irregulares / total_notas * 100)) if total_notas > 0 else 0

        return {
            "indice_risco": risco_dinamico,
            "percentual_inconsistencia": (total_irregulares / total_notas * 100) if total_notas > 0 else 0,
            "potencial_glosa": glosa,
            "evolucao_exposicao": evolucao_final,
            "tendencia_exposicao": tendencia_exposicao
        }
    except Exception as e:
        print(f"Erro Intel: {e}")
        return {"error": str(e)}

@router.get("/summary", summary="Relatório de ROI e Valor Realizado")
def get_roi_summary(empresa_id: str = None, user: dict = Depends(get_current_user)):
    """
    Calcula o ROI consolidado do escritório ou por cliente.
    Se for Monitor, força o filtro pela empresa vinculada.
    """
    try:
        # Usamos o cliente autenticado do usuário para respeitar RLS
        user_client = supabase_service.get_client_for_user(get_current_token())
        
        # Buscar perfil para identificação básica
        profile_res = user_client.table("profiles").select("role, empresa_id, tenant_id").eq("id", user['id']).single().execute()
        profile = profile_res.data or {}
        role = profile.get('role')
        linked_company = profile.get('empresa_id')
        tenant_id = profile.get('tenant_id')
            
        # Se for Monitor, IGNORA o parametro empresa_id e usa o vinculado
        if role == 'monitor':
            if not linked_company:
                 return {
                    "total_creditos_identificados": 0,
                    "alertas_resolvidos": 0,
                    "economia_estimada": 0,
                    "potencial_glosa": 0,
                    "valor_mensal_plano": 499.00,
                    "roi_ratio": 0
                }
            empresa_id = linked_company
        
        # 1. Total de Créditos CBS/IBS (Estimativa de 1% do valor total das notas)
        # Usar user_client para respeitar RLS
        query_notas = user_client.table("notas_fiscais").select("valor_total")
        
        if empresa_id:
            query_notas = query_notas.eq("empresa_id", empresa_id)
        
        res = query_notas.execute()
        print(f"DEBUG ROI SUMMARY: Encontradas {len(res.data) if res.data else 0} notas para cálculo.")
        
        # Padronizando com Dashboard: 1% estimado se crédito real for zero
        total_creditos = sum((float(item.get('valor_total', 0) or 0) * 0.01) for item in (res.data or []))
        
        # 2. Total de Alertas (Potencial Glosa)
        query_alertas = user_client.table("alertas_conformidade").select("diferenca").eq("resolvido", False)
        if empresa_id:
            query_alertas = query_alertas.eq("empresa_id", empresa_id)
            
        res_alertas = query_alertas.execute()
        total_glosa = sum(item.get('diferenca', 0) or 0 for item in (res_alertas.data or []))

        # 3. Total de Alertas Resolvidos (Economia Realizada)
        query_alertas_resolvidos = user_client.table("alertas_conformidade").select("diferenca").eq("resolvido", True)
        if empresa_id:
            query_alertas_resolvidos = query_alertas_resolvidos.eq("empresa_id", empresa_id)
        
        res_alertas_resolvidos = query_alertas_resolvidos.execute()
        alertas_resolvidos_count = len(res_alertas_resolvidos.data) if res_alertas_resolvidos.data else 0
        economia_realizada = sum(abs(item.get('diferenca', 0) or 0) for item in (res_alertas_resolvidos.data or []))
        
        return {
            "total_creditos_identificados": total_creditos,
            "alertas_resolvidos": alertas_resolvidos_count,
            "economia_estimada": economia_realizada,
            "potencial_glosa": total_glosa,
            "valor_mensal_plano": 499.00,
            "roi_ratio": (total_creditos + economia_realizada) / 499.00 if (total_creditos + economia_realizada) > 0 else 0
        }
    except Exception as e:
        print(f"Erro ROI: {e}")
        return {"error": str(e)}
