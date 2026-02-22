-- Seed: 006_legacy_tax_rules.sql
-- Regras para tributos vigentes (PIS/COFINS) para demonstração de auditoria multi-tributos

-- 1. Regra de PIS (Lucro Real) - 1.65%
INSERT INTO fiscal_rules (name, description, rule_type, expected_rate, severity, parameters)
VALUES (
  'PIS - Alíquota Geral (Lucro Real)',
  'Programa de Integração Social - Alíquota padrão para regime não-cumulativo.',
  'pis',
  0.0165,
  'media',
  '{"tolerance": 0.05, "regime": "lucro_real"}'::jsonb
);

-- 2. Regra de COFINS (Lucro Real) - 7.6%
INSERT INTO fiscal_rules (name, description, rule_type, expected_rate, severity, parameters)
VALUES (
  'COFINS - Alíquota Geral (Lucro Real)',
  'Contribuição para o Financiamento da Seguridade Social - Alíquota padrão regime não-cumulativo.',
  'cofins',
  0.076,
  'media',
  '{"tolerance": 0.10, "regime": "lucro_real"}'::jsonb
);

-- 3. Regra de ICMS (Exemplo: SP 18%) para NCMs Genéricos de Mercadorias
INSERT INTO fiscal_rules (name, description, rule_type, expected_rate, severity, parameters)
VALUES (
  'ICMS Geral - Alíquota Interna SP',
  'ICMS padrão de 18% para operações internas dentro do estado de São Paulo.',
  'icms',
  0.18,
  'baixa',
  '{"tolerance": 0.05, "uf": "SP"}'::jsonb
);
