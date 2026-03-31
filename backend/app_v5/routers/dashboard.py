from fastapi import APIRouter, Depends, HTTPException, Response
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token, get_current_user
import json
import os
import logging
import time

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()

# In-memory cache (substitui Redis)
_dashboard_cache: dict = {}
_cache_ttl = 300  # 5 minutos

@router.get("/current-company", summary="Métricas para o Termômetro de Risco")
def get_dashboard_metrics(response: Response, user: dict = Depends(get_current_user)):
    # Prevent caching of sensitive metrics data
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"
    logger.info("DASHBOARD: Iniciando fetching de métricas...")
    """
    Retorna os KPIs principais para o dashboard da empresa buscando no Supabase.
    Requer autenticação para identificar o tenant do usuário.
    Se for Monitor, filtra apenas pela empresa vinculada.
    """
    try:
        # 1. Obter cliente autenticado
        user_id = user['id']
        
        # 2. Obter perfil completo (Unificado com roi.py)
        # Se .single() falhar porque não existe registro, o client pode levantar erro ou retornar data=None
        # 2. Obter perfil completo via ADMIN para garantir leitura
        admin_client = supabase_service.get_service_client()
        profile_res = admin_client.table("profiles").select("role, empresa_id, tenant_id").eq("id", user_id).single().execute()
        profile = profile_res.data or {}
        
        role = profile.get('role')
        empresa_id = profile.get('empresa_id')
        tenant_id = profile.get('tenant_id')
        cache_key = f"dash_metrics_{tenant_id}_{empresa_id or 'all'}"
        
        logger.info(f"DASHBOARD: User={user_id}, Tenant={tenant_id}, Role={role}")

        # 3. Verificar Cache em Memória
        cached_entry = _dashboard_cache.get(cache_key)
        if cached_entry and (time.time() - cached_entry['ts']) < _cache_ttl:
            logger.info(f"DASHBOARD: Retornando dados via Cache para {tenant_id}")
            return cached_entry['data']
        
        # Preparar Query Base (Últimos 30 dias)
        from datetime import datetime, timedelta
        data_limite = (datetime.now() - timedelta(days=30)).isoformat()

        # Usamos service_client com filtro manual para garantir bypass de RLS instável
        # mantendo a segurança via filtro de tenant_id validado.
        admin_client = supabase_service.get_service_client()
        
        query_notas = admin_client.table("notas_fiscais").select("id, status, valor_total, emitente_cnpj, destinatario_cnpj").eq("tenant_id", tenant_id).gte("created_at", data_limite)
        
        # FILTRO DE MONITOR
        if role == 'monitor':
            if not empresa_id:
                 return {
                    "empresa_id": None,
                    "risco_score": 0,
                    "total_notas": 0,
                    "notas_emitidas": 0,
                    "notas_recebidas": 0,
                    "notas_com_erro": 0,
                    "valor_bens_servicos": 0,
                    "credito_tributario_potencial": 0,
                    "status": "seguro"
                }
            query_notas = query_notas.eq("empresa_id", empresa_id)
        
        # Executar Queries
        try:
            # 1. Fetching Cnpjs para classificar emissão vs recebimento
            query_empresas = admin_client.table("empresas").select("cnpj").eq("tenant_id", tenant_id)
            if role == 'monitor' and empresa_id:
                query_empresas = query_empresas.eq("id", empresa_id)
            cnpjs_empresa = [e.get('cnpj') for e in (query_empresas.execute().data or []) if e.get('cnpj')]
            
            # 2. Fetching Notas
            res_notas = query_notas.execute()
            notas_data = res_notas.data or []
            
            total_notas = len(notas_data)
            notas_emitidas = 0
            notas_recebidas = 0
            notas_com_erro = 0
            valor_total_soma = 0.0
            
            for nota in notas_data:
                valor_total_soma += float(nota.get('valor_total') or 0.0)
                is_erro = nota.get('status') == 'irregular'
                
                if is_erro:
                    notas_com_erro += 1
                    
                if nota.get('emitente_cnpj') in cnpjs_empresa:
                    notas_emitidas += 1
                else:
                    notas_recebidas += 1
            
            # Cálculo de Glosa e Créditos via query de alertas
            # Glosa = Erros de Compliance (Risco)
            # Crédito = Oportunidades Identificadas (Economia)
            query_alertas = admin_client.table("alertas_conformidade").select("diferenca, is_opportunity").eq("tenant_id", tenant_id).eq("resolvido", False)
            if role == 'monitor' and empresa_id:
                query_alertas = query_alertas.eq("empresa_id", empresa_id)
            res_alertas = query_alertas.execute()
            
            alertas_data = res_alertas.data or []
            total_glosa = sum(float(a.get('diferenca', 0) or 0) for a in alertas_data if not a.get('is_opportunity', False))
            total_creditos = sum(float(a.get('diferenca', 0) or 0) for a in alertas_data if a.get('is_opportunity', False))

            # Cálculo de Score END (Ponderado - Camada 3)
            # 50% Frequência de Erros | 50% Impacto Financeiro (vs Faturamento)
            frequencia_score = (notas_com_erro / total_notas * 50) if total_notas > 0 else 0
            impacto_score = (total_glosa / (valor_total_soma or 1) * 500) if valor_total_soma > 0 else 0 # Escala de impacto
            
            risco_score = int(min(frequencia_score + impacto_score, 100))
                
            # 3. Fetching última sincronização do certificado
            ultima_sync = None
            cert_res = admin_client.table("certificados_a1").select("ultimo_sync").eq("tenant_id", tenant_id)
            if role == 'monitor' and empresa_id:
                cert_res = cert_res.eq("empresa_id", empresa_id)
            
            cert_data = cert_res.maybe_single().execute().data
            if cert_data:
                ultima_sync = cert_data.get('ultimo_sync')

            result = {
                "empresa_id": empresa_id if role == 'monitor' else tenant_id, 
                "risco_score": risco_score,
                "total_notas": total_notas,
                "notas_emitidas": notas_emitidas,
                "notas_recebidas": notas_recebidas,
                "notas_com_erro": notas_com_erro,
                "valor_bens_servicos": round(valor_total_soma, 2),
                "credito_tributario_potencial": round(total_creditos, 2),
                "ultima_sincronizacao": ultima_sync,
                "status": "seguro" if risco_score <= 15 else "atencao" if risco_score <= 40 else "critico"
            }

            # 4. Salvar no Cache em Memória (TTL 5 minutos)
            _dashboard_cache[cache_key] = {'data': result, 'ts': time.time()}

            return result

        except Exception as query_error:
            logger.error(f"DASHBOARD: Erro na execução das queries SQL: {query_error}")
            return {
                "empresa_id": empresa_id if role == 'monitor' else tenant_id, 
                "risco_score": 0,
                "total_notas": 0,
                "notas_emitidas": 0,
                "notas_recebidas": 0,
                "notas_com_erro": 0,
                "valor_bens_servicos": 0,
                "credito_tributario_potencial": 0,
                "status": "seguro"
            }
    except Exception as e:
        logger.error(f"DASHBOARD: Erro fatal ao buscar métricas: {e}")
        # Retornamos 200 com dados zerados em vez de 500 para não quebrar o frontend
        return {
            "empresa_id": None, 
            "risco_score": 0,
            "total_notas": 0,
            "notas_emitidas": 0,
            "notas_recebidas": 0,
            "notas_com_erro": 0,
            "valor_bens_servicos": 0,
            "credito_tributario_potencial": 0,
            "status": "seguro"
        }
