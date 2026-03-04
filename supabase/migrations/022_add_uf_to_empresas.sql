-- Migration 022: Adicionar coluna UF na tabela empresas
-- Necessário para determinar o endpoint SEFAZ correto (RecepcaoEvento4)

ALTER TABLE empresas ADD COLUMN IF NOT EXISTS uf TEXT DEFAULT 'SP';

-- Comentário para clareza
COMMENT ON COLUMN empresas.uf IS 'Sigla do estado da empresa (ex: SP, GO, MG) para integração SEFAZ';

-- Backfill para a empresa do usuário (identificada via CNPJ 16968599000191 como sendo de GO)
UPDATE empresas SET uf = 'GO' WHERE cnpj = '16968599000191';
UPDATE empresas SET uf = 'GO' WHERE cnpj = '16.968.599/0001-91';
