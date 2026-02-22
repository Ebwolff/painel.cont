-- Seed: 003_seed_fiscal_rules.sql
-- Regras iniciais da Reforma Tributária 2026 (CBS 0.9% / IBS 0.1%)

-- 1. Regra Genérica de CBS (Aplica a todos os NCMs)
INSERT INTO fiscal_rules (name, description, rule_type, expected_rate, severity, parameters)
VALUES (
  'CBS Geral - Reforma 2026',
  'Contribuição sobre Bens e Serviços - Alíquota geral de transição 2026',
  'cbs',
  0.009,
  'alta',
  '{"tolerance": 0.05}'::jsonb
);

-- 2. Regra Genérica de IBS (Aplica a todos os NCMs)
INSERT INTO fiscal_rules (name, description, rule_type, expected_rate, severity, parameters)
VALUES (
  'IBS Geral - Reforma 2026',
  'Imposto sobre Bens e Serviços - Alíquota geral de transição 2026',
  'ibs',
  0.001,
  'alta',
  '{"tolerance": 0.05}'::jsonb
);

-- 3. CBS específica para Alimentos (NCM Capítulo 02-23) - Cesta Básica com redução
INSERT INTO fiscal_rules (name, description, rule_type, ncm, expected_rate, severity, parameters)
VALUES (
  'CBS Alimentos - Cesta Básica',
  'CBS reduzida para itens de cesta básica (NCM Capítulo 02). Alíquota 0% na transição.',
  'cbs',
  '02',
  0.0,
  'media',
  '{"tolerance": 0.01, "nota": "Cesta básica tem isenção de CBS na transição"}'::jsonb
);

-- 4. IBS específica para Alimentos (NCM Capítulo 02-23) - Cesta Básica com redução
INSERT INTO fiscal_rules (name, description, rule_type, ncm, expected_rate, severity, parameters)
VALUES (
  'IBS Alimentos - Cesta Básica',
  'IBS reduzida para itens de cesta básica (NCM Capítulo 02). Alíquota 0% na transição.',
  'ibs',
  '02',
  0.0,
  'media',
  '{"tolerance": 0.01}'::jsonb
);

-- 5. CBS para medicamentos (NCM Capítulo 30) - Alíquota reduzida
INSERT INTO fiscal_rules (name, description, rule_type, ncm, expected_rate, severity, parameters)
VALUES (
  'CBS Medicamentos',
  'CBS com alíquota reduzida de 60% para medicamentos registrados na ANVISA.',
  'cbs',
  '30',
  0.0054,
  'alta',
  '{"tolerance": 0.05, "nota": "60% da alíquota cheia de CBS"}'::jsonb
);

-- 6. IBS para medicamentos (NCM Capítulo 30) - Alíquota reduzida
INSERT INTO fiscal_rules (name, description, rule_type, ncm, expected_rate, severity, parameters)
VALUES (
  'IBS Medicamentos',
  'IBS com alíquota reduzida de 60% para medicamentos registrados na ANVISA.',
  'ibs',
  '30',
  0.0006,
  'alta',
  '{"tolerance": 0.05}'::jsonb
);
