-- Migration: 012_pricing_by_volume.sql
-- Objetivo: Implementar limites técnicos baseados no volume de CNPJs/CPFs por escritório.

-- 1. Adicionar coluna de limite na tabela de tenants
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS limite_empresas integer DEFAULT 5;

-- 2. Atualizar limites baseados nos planos atuais (Retroatividade)
-- Starter/Free: 5 empresas
-- Pro: 15 empresas
-- Enterprise: 99999 (Ilimitado na prática)
UPDATE tenants SET limite_empresas = 5 WHERE plano IN ('free', 'starter');
UPDATE tenants SET limite_empresas = 15 WHERE plano = 'pro';
UPDATE tenants SET limite_empresas = 99999 WHERE plano = 'enterprise';

COMMENT ON COLUMN tenants.limite_empresas IS 'Quantidade máxima de empresas (CNPJ/CPF) que o escritório pode monitorar';

-- 3. Adicionar colunas de controle administrativo e setup
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS suspensao_limite boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS setup_pago boolean DEFAULT false;

COMMENT ON COLUMN tenants.setup_pago IS 'Indica se a taxa de implementação (Setup) já foi paga pelo escritório';
