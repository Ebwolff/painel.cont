-- Migration: 013_performance_indexes.sql
-- Objetivo: Otimização de performance para escala nacional (Fase 1)

-- 1. Notas Fiscais
-- Índice para o termômetro de risco e dashboard (leitura frequente por tenant e data)
CREATE INDEX IF NOT EXISTS idx_notas_tenant_created ON notas_fiscais(tenant_id, created_at DESC);
-- Índice para filtros de status no dashboard
CREATE INDEX IF NOT EXISTS idx_notas_tenant_status ON notas_fiscais(tenant_id, status);
-- Índice para visão isolada de empresa (Perfil Monitor)
CREATE INDEX IF NOT EXISTS idx_notas_empresa_status ON notas_fiscais(empresa_id, status);

-- 2. Alertas de Conformidade
-- Índice para contagem de alertas pendentes por tenant
CREATE INDEX IF NOT EXISTS idx_alertas_tenant_resolvido ON alertas_conformidade(tenant_id, resolvido);
-- Índice para contagem de alertas por empresa
CREATE INDEX IF NOT EXISTS idx_alertas_empresa_resolvido ON alertas_conformidade(empresa_id, resolvido);
-- Índice para relacionamento nota-alerta
CREATE INDEX IF NOT EXISTS idx_alertas_nota ON alertas_conformidade(nota_fiscal_id);

-- 3. Itens da Nota
-- Índice para auditoria e detalhamento de itens
CREATE INDEX IF NOT EXISTS idx_items_nota ON nfe_items(nota_fiscal_id);
-- Índice para buscas por NCM (Análise Cross-Tenant)
CREATE INDEX IF NOT EXISTS idx_items_ncm ON nfe_items(ncm);

-- 4. Regras Fiscais
-- Otimização do RuleEngine (busca de regras ativas por tipo)
CREATE INDEX IF NOT EXISTS idx_rules_active_type ON fiscal_rules(active, rule_type);
-- Busca por NCM na matriz tributária
CREATE INDEX IF NOT EXISTS idx_rules_ncm ON fiscal_rules(ncm);

-- 5. Perfil de Usuário
-- Otimização do get_current_user e queries de segurança
CREATE INDEX IF NOT EXISTS idx_profiles_tenant ON profiles(id, tenant_id);
