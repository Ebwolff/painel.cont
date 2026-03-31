-- Migration: 023_add_base_legal_to_alertas.sql
-- Adiciona coluna base_legal para armazenar a fundamentação jurídica de cada alerta

ALTER TABLE alertas_conformidade
ADD COLUMN IF NOT EXISTS base_legal text;

COMMENT ON COLUMN alertas_conformidade.base_legal IS 'Fundamentação legal/jurídica que originou o alerta (ex: Lei 14.133, Convênio ICMS 142)';
