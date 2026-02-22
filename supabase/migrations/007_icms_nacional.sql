-- Migration 007: Suporte Nacional ao ICMS (Multi-UF)
-- Adiciona coluna 'uf' na tabela de regras para distinguir alíquotas por estado.

ALTER TABLE fiscal_rules ADD COLUMN IF NOT EXISTS uf char(2);

-- Index para buscas por UF e tipo de regra (performance)
CREATE INDEX IF NOT EXISTS idx_fiscal_rules_uf ON fiscal_rules(uf);
CREATE INDEX IF NOT EXISTS idx_fiscal_rules_rule_type_uf ON fiscal_rules(rule_type, uf);

-- ============================================================
-- SEED: Alíquotas Vigentes de ICMS Interno por Unidade Federativa
-- Fonte: Decretos Estaduais vigentes em 2025
-- Alíquota interna geral (mercadorias em geral)
-- ============================================================

INSERT INTO fiscal_rules (name, rule_type, uf, expected_rate, severity, active, version, parameters)
VALUES
  -- Norte
  ('ICMS Interno - AC', 'icms', 'AC', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual AC", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - AM', 'icms', 'AM', 0.20, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual AM", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - AP', 'icms', 'AP', 0.18, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual AP", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - PA', 'icms', 'PA', 0.19, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual PA", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - RO', 'icms', 'RO', 0.175, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual RO", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - RR', 'icms', 'RR', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual RR", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - TO', 'icms', 'TO', 0.18, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual TO", "tipo": "aliquota_interna_geral"}'),

  -- Nordeste
  ('ICMS Interno - AL', 'icms', 'AL', 0.19, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual AL", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - BA', 'icms', 'BA', 0.205, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual BA", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - CE', 'icms', 'CE', 0.20, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual CE", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - MA', 'icms', 'MA', 0.22, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual MA", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - PB', 'icms', 'PB', 0.20, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual PB", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - PE', 'icms', 'PE', 0.205, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual PE", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - PI', 'icms', 'PI', 0.21, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual PI", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - RN', 'icms', 'RN', 0.20, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual RN", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - SE', 'icms', 'SE', 0.19, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual SE", "tipo": "aliquota_interna_geral"}'),

  -- Centro-Oeste
  ('ICMS Interno - DF', 'icms', 'DF', 0.20, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto DF", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - GO', 'icms', 'GO', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual GO", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - MS', 'icms', 'MS', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual MS", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - MT', 'icms', 'MT', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual MT", "tipo": "aliquota_interna_geral"}'),

  -- Sudeste
  ('ICMS Interno - ES', 'icms', 'ES', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual ES", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - MG', 'icms', 'MG', 0.18, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual MG", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - RJ', 'icms', 'RJ', 0.22, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual RJ", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - SP', 'icms', 'SP', 0.18, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual SP", "tipo": "aliquota_interna_geral"}'),

  -- Sul
  ('ICMS Interno - PR', 'icms', 'PR', 0.185, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual PR", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - RS', 'icms', 'RS', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual RS", "tipo": "aliquota_interna_geral"}'),
  ('ICMS Interno - SC', 'icms', 'SC', 0.17, 'baixa', true, 'oficial-2025', '{"fonte": "Decreto Estadual SC", "tipo": "aliquota_interna_geral"}')

ON CONFLICT DO NOTHING;

-- Comentário: A coluna 'uf' NULL nas regras significa "regra nacional" (aplica a todos os estados).
-- O motor de regras deve dar prioridade à regra específica de UF sobre a regra nacional quando ambas existirem.
