-- Migration: 015_materialized_view_triggers.sql
-- Objetivo: Automatizar o refresh das views do dashboard (Fase 2)

-- 1. Função de trigger para Notas Fiscais
CREATE OR REPLACE FUNCTION trigger_refresh_dashboard_stats()
RETURNS trigger AS $$
BEGIN
  -- Refresh concorrente para não travar a tabela
  PERFORM refresh_dashboard_stats();
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger para notas_fiscais
DROP TRIGGER IF EXISTS tr_refresh_dashboard ON notas_fiscais;
CREATE TRIGGER tr_refresh_dashboard
AFTER INSERT OR UPDATE OR DELETE ON notas_fiscais
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_refresh_dashboard_stats();

-- 3. Função de trigger para Alertas
CREATE OR REPLACE FUNCTION trigger_refresh_alerts_stats()
RETURNS trigger AS $$
BEGIN
  PERFORM refresh_alerts_stats();
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 4. Trigger para alertas_conformidade
DROP TRIGGER IF EXISTS tr_refresh_alerts ON alertas_conformidade;
CREATE TRIGGER tr_refresh_alerts
AFTER INSERT OR UPDATE OR DELETE OR TRUNCATE ON alertas_conformidade
FOR EACH STATEMENT
EXECUTE FUNCTION trigger_refresh_alerts_stats();
