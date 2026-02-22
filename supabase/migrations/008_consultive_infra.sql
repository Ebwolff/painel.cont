-- Migration 008: Infraestrutura para Contabilidade Consultiva
-- Adiciona campos para distinguir entre riscos fiscais e oportunidades de crédito.

-- 1. Adicionar categoria às regras fiscais
ALTER TABLE fiscal_rules ADD COLUMN IF NOT EXISTS category text DEFAULT 'compliance'; -- 'compliance' (risco) | 'opportunity' (crédito)

-- 2. Adicionar flag de oportunidade aos alertas
ALTER TABLE alertas_conformidade ADD COLUMN IF NOT EXISTS is_opportunity boolean DEFAULT false;

-- 3. Índices para performance em relatórios de créditos
CREATE INDEX IF NOT EXISTS idx_alertas_opportunity ON alertas_conformidade(is_opportunity) WHERE is_opportunity = true;
CREATE INDEX IF NOT EXISTS idx_fiscal_rules_category ON fiscal_rules(category);

COMMENT ON COLUMN fiscal_rules.category IS 'Define se a regra busca um erro do contribuinte (compliance) ou uma economia/crédito (opportunity)';
COMMENT ON COLUMN alertas_conformidade.is_opportunity IS 'Se verdadeiro, indica que o alerta representa um potencial crédito tributário a recuperar';
