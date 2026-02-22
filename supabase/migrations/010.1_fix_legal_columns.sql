-- Migration: 010.1_fix_legal_columns.sql
-- Objetivo: Adicionar colunas faltantes que causaram erro na Carga Mestre.

ALTER TABLE fiscal_rules 
ADD COLUMN IF NOT EXISTS legal_foundation text,
ADD COLUMN IF NOT EXISTS last_checked_at timestamptz DEFAULT now();

COMMENT ON COLUMN fiscal_rules.legal_foundation IS 'Base legal/Artigo da lei que fundamenta a regra';
COMMENT ON COLUMN fiscal_rules.last_checked_at IS 'Data da última verificação de validade da regra';
