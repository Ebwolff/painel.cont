-- Migration 009: Catálogo de Oportunidades (PIS/COFINS Monofásico)
-- Insere regras que identificam produtos onde o imposto deve ser ZERO para o varejista.
-- Natureza: Opportunity (Crédito Tributário)

INSERT INTO fiscal_rules (name, rule_type, category, ncm, expected_rate, severity, active, version, parameters)
VALUES
  -- BEBIDAS (Monofásico)
  ('PIS Monofásico - Cervejas', 'pis', 'opportunity', '2203', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.833/03", "detalhe": "Tributação concentrada no fabricante/importador"}'),
  ('COFINS Monofásico - Cervejas', 'cofins', 'opportunity', '2203', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.833/03", "detalhe": "Tributação concentrada no fabricante/importador"}'),
  ('PIS Monofásico - Refrigerantes', 'pis', 'opportunity', '2202', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.833/03"}'),
  ('COFINS Monofásico - Refrigerantes', 'cofins', 'opportunity', '2202', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.833/03"}'),

  -- AUTOPEÇAS (Monofásico)
  ('PIS Monofásico - Autopeças', 'pis', 'opportunity', '8708', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.485/02"}'),
  ('COFINS Monofásico - Autopeças', 'cofins', 'opportunity', '8708', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.485/02"}'),

  -- PERFUMARIA E HIGIENE (Monofásico)
  ('PIS Monofásico - Higiene Pessoal', 'pis', 'opportunity', '3304', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.147/00"}'),
  ('COFINS Monofásico - Higiene Pessoal', 'cofins', 'opportunity', '3304', 0.0, 'baixa', true, 'consultiva-1.0', '{"fundamento": "Lei 10.147/00"}')

ON CONFLICT DO NOTHING;
