-- Migration: 011_ncm_matrix_core.sql
-- Objetivo: Carga Mestre de Regras por Categoria (Hierarquia NCM) para cobertura nacional.

-- Regras de Capítulo (2 dígitos) - Funcionam como "Rede de Proteção" (Fallback)
-- Se o sistema não achar o NCM de 8 dígitos, ele aplicará estas regras.

INSERT INTO fiscal_rules (name, rule_type, category, ncm, expected_rate, severity, legal_foundation, parameters)
VALUES
  -- CAP 30: PRODUTOS FARMACÊUTICOS (Alíquota zero para vários itens de transição)
  ('Regra Geral: Setor Farmacêutico (Cap. 30)', 'cbs', 'compliance', '30', 0.009, 'baixa', 'Reforma Tributária - Regra Setorial', '{"fallback": true}'),
  ('Regra Geral: Setor Farmacêutico (Cap. 30)', 'ibs', 'compliance', '30', 0.001, 'baixa', 'Reforma Tributária - Regra Setorial', '{"fallback": true}'),

  -- CAP 02: CARNES E MIUDEZAS (Alimentos - Cesta Básica)
  ('Regra Geral: Cesta Básica (Carnes Cap. 02)', 'cbs', 'compliance', '02', 0.0, 'critica', 'Reforma Tributária - Isenção Cesta Básica', '{"fallback": true}'),
  ('Regra Geral: Cesta Básica (Carnes Cap. 02)', 'ibs', 'compliance', '02', 0.0, 'critica', 'Reforma Tributária - Isenção Cesta Básica', '{"fallback": true}'),

  -- CAP 84: MÁQUINAS E APARELHOS MECÂNICOS (Bens de Capital)
  ('Regra Geral: Bens de Capital (Cap. 84)', 'cbs', 'compliance', '84', 0.009, 'baixa', 'Reforma Tributária - Bens de Capital', '{"fallback": true}'),
  ('Regra Geral: Bens de Capital (Cap. 84)', 'ibs', 'compliance', '84', 0.001, 'baixa', 'Reforma Tributária - Bens de Capital', '{"fallback": true}'),

  -- CAP 22: BEBIDAS (Atenção para Monofásicos)
  ('Regra Geral: Bebidas (Cap. 22)', 'cbs', 'compliance', '22', 0.009, 'media', 'Regra Geral de Transição', '{"fallback": true}'),
  ('Regra Geral: Bebidas (Cap. 22)', 'ibs', 'compliance', '22', 0.001, 'media', 'Regra Geral de Transição', '{"fallback": true}');

-- Exemplos Interestaduais (SP -> Destinos Norte/Nordeste)
INSERT INTO fiscal_rules (name, rule_type, category, origin_uf, expected_rate, severity, legal_foundation)
VALUES
  ('ICMS interestadual SP -> Norte/Nordeste', 'icms', 'compliance', 'SP', 0.07, 'alta', 'Convênio ICMS 93/2015');

-- Marcar data de carga
UPDATE fiscal_rules SET last_checked_at = now() WHERE version = '1.0.0';
