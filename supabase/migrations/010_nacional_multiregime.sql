-- Migration: 010_nacional_multiregime.sql
-- Objetivo: Suporte a exceções de ICMS por estado e regimes tributários variados.

-- 1. Adicionar colunas de segmentação geográfica e tributária
ALTER TABLE fiscal_rules 
ADD COLUMN IF NOT EXISTS origin_uf text,
ADD COLUMN IF NOT EXISTS dest_uf text,
ADD COLUMN IF NOT EXISTS regime_tributario text DEFAULT 'lucro_real',
ADD COLUMN IF NOT EXISTS ex_tipi text;

-- 2. Criar índices para performance em buscas geográficas
CREATE INDEX IF NOT EXISTS idx_fiscal_rules_uf ON fiscal_rules(origin_uf, dest_uf);
CREATE INDEX IF NOT EXISTS idx_fiscal_rules_regime ON fiscal_rules(regime_tributario);

-- 3. Exemplo de Regra de ICMS Interestadual (SP -> Outros Estados)
INSERT INTO fiscal_rules (name, rule_type, category, origin_uf, expected_rate, severity, active, version, parameters)
VALUES 
  ('ICMS Interestadual - Saída SP (7%)', 'icms', 'compliance', 'SP', 0.07, 'media', true, 'nac-1.0', '{"detalhe": "Alíquota interestadual padrão para regiões Norte, Nordeste, Centro-Oeste e ES"}'),
  ('ICMS Interestadual - Saída SP (12%)', 'icms', 'compliance', 'SP', 0.12, 'media', true, 'nac-1.0', '{"detalhe": "Alíquota interestadual para Sul e Sudeste (exceto ES)"}');

-- 4. Adicionar coluna de regime nas empresas para o motor ler
ALTER TABLE empresas
ADD COLUMN IF NOT EXISTS regime_tributario text DEFAULT 'lucro_real';

COMMENT ON COLUMN fiscal_rules.origin_uf IS 'UF de origem para regras de ICMS';
COMMENT ON COLUMN fiscal_rules.dest_uf IS 'UF de destino para regras de ICMS';
COMMENT ON COLUMN fiscal_rules.regime_tributario IS 'Regime afetado: simples_nacional, lucro_presumido, lucro_real';
