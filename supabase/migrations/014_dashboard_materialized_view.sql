-- Migration: 014_dashboard_materialized_view.sql
-- Objetivo: Acelerar o carregamento do dashboard (Fase 1)

-- 1. Criação da Materialized View
-- Agrupa os principais KPIs por tenant e empresa para os últimos 30 dias
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_stats AS
SELECT 
    tenant_id,
    empresa_id,
    COUNT(*) as total_notas,
    COUNT(*) FILTER (WHERE status = 'irregular') as notas_com_erro,
    SUM(COALESCE(valor_total, 0)) as valor_total_soma,
    SUM(COALESCE(valor_cbs, 0)) as valor_cbs_soma,
    SUM(COALESCE(valor_ibs, 0)) as valor_ibs_soma,
    MAX(created_at) as last_update
FROM notas_fiscais
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY tenant_id, empresa_id;

-- 2. Índice para busca rápida na view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_dash_tenant_empresa ON mv_dashboard_stats(tenant_id, empresa_id);

-- 3. Função para Refresh da View
-- Pode ser chamada via RPC ou Trigger (em fases futuras)
CREATE OR REPLACE FUNCTION refresh_dashboard_stats()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_stats;
END;
$$ LANGUAGE plpgsql;

-- 4. Alertas Summary Materialized View (Opcional, mas recomendado)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_alerts_stats AS
SELECT 
    tenant_id,
    empresa_id,
    severidade,
    is_opportunity,
    COUNT(*) as total,
    SUM(COALESCE(diferenca, 0)) as total_diferenca
FROM alertas_conformidade
WHERE resolvido = false
GROUP BY tenant_id, empresa_id, severidade, is_opportunity;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_alerts_composite ON mv_alerts_stats(tenant_id, empresa_id, severidade, is_opportunity);

CREATE OR REPLACE FUNCTION refresh_alerts_stats()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_alerts_stats;
END;
$$ LANGUAGE plpgsql;
