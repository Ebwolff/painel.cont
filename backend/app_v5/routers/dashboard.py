from fastapi import APIRouter, Depends, HTTPException
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_token, get_current_user
import redis
import json
import os
import logging

logger = logging.getLogger(__name__)


router = APIRouter()
supabase_service = SupabaseService()

@router.get("/current-company", summary="Métricas para o Termômetro de Risco")
def get_dashboard_metrics(user: dict = Depends(get_current_user)):
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
        
        logger.info(f"DASHBOARD: User={user_id}, Tenant={tenant_id}, Role={role}")

        # 3. Verificar Cache Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.Redis.from_url(redis_url, decode_responses=True)
        cache_key = f"dash:stats:{tenant_id}:{empresa_id or 'all'}"
        
        cached_data = r.get(cache_key)
        if cached_data:
            logger.info(f"DASHBOARD: Retornando dados via Cache Redis para {tenant_id}")
            return json.loads(cached_data)
        
        # Preparar Query Base (Últimos 30 dias)
        from datetime import datetime, timedelta
        data_limite = (datetime.now() - timedelta(days=30)).isoformat()

        # Preparar Query Base (Últimos 30 dias)
        from datetime import datetime, timedelta
        data_limite = (datetime.now() - timedelta(days=30)).isoformat()

        # Usamos service_client com filtro manual para garantir bypass de RLS instável
        # mantendo a segurança via filtro de tenant_id validado.
        admin_client = supabase_service.get_service_client()
        
        query_notas = admin_client.table("notas_fiscais").select("id", count="exact").eq("tenant_id", tenant_id).gte("created_at", data_limite)
        query_erro = admin_client.table("notas_fiscais").select("id", count="exact").eq("tenant_id", tenant_id).eq("status", "irregular").gte("created_at", data_limite)
        query_valor = admin_client.table("notas_fiscais").select("valor_total").eq("tenant_id", tenant_id).gte("created_at", data_limite)
        
        # FILTRO DE MONITOR
        if role == 'monitor':
            if not empresa_id:
                 return {
                    "empresa_id": None,
                    "risco_score": 0,
                    "total_notas": 0,
                    "notas_com_erro": 0,
                    "valor_bens_servicos": 0,
                    "credito_tributario_potencial": 0,
                    "status": "seguro"
                }
            query_notas = query_notas.eq("empresa_id", empresa_id)
            query_erro = query_erro.eq("empresa_id", empresa_id)
            query_valor = query_valor.eq("empresa_id", empresa_id)
        
        # Executar Queries
        try:
            total_res = query_notas.execute()
            total_notas = total_res.count if total_res.count is not None else 0
            
            erro_res = query_erro.execute()
            notas_com_erro = erro_res.count if erro_res.count is not None else 0
            
            # Para o valor total, buscamos apenas os valores necessários
            valor_res = query_valor.execute()
            valor_total_soma = sum([float(item.get('valor_total', 0) or 0) for item in (valor_res.data or [])])
            
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
                
            result = {
                "empresa_id": empresa_id if role == 'monitor' else tenant_id, 
                "risco_score": risco_score,
                "total_notas": total_notas,
                "notas_com_erro": notas_com_erro,
                "valor_bens_servicos": round(valor_total_soma, 2),
                "credito_tributario_potencial": round(total_creditos, 2),
                "status": "seguro" if risco_score <= 15 else "atencao" if risco_score <= 40 else "critico"
            }

            # 4. Salvar no Cache (TTL 5 minutos)
            try:
                r.setex(cache_key, 300, json.dumps(result))
            except Exception as cache_error:
                logger.warning(f"DASHBOARD: Falha ao salvar no cache Redis: {cache_error}")

            return result

        except Exception as query_error:
            logger.error(f"DASHBOARD: Erro na execução das queries SQL: {query_error}")
            return {
                "empresa_id": empresa_id if role == 'monitor' else tenant_id, 
                "risco_score": 0,
                "total_notas": 0,
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
            "notas_com_erro": 0,
            "valor_bens_servicos": 0,
            "credito_tributario_potencial": 0,
            "status": "seguro"
        }
