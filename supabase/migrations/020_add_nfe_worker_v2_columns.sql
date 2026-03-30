-- Migration to support NFE Worker NestJS V2 Hybrid Sync
-- Ajustado para o Schema 'notas_fiscais' real (que possuía chave_acesso ao invés de chave, e usava 'tipo' para nfe/nfse)

-- Cria Enum type para DirecaoNota
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'direcao_nota') THEN
        CREATE TYPE direcao_nota AS ENUM ('emitida', 'recebida');
    END IF;
END$$;

-- Adiciona as colunas do Worker V2 que não existiam na V1
ALTER TABLE "notas_fiscais" 
ADD COLUMN IF NOT EXISTS "nsu" text,
ADD COLUMN IF NOT EXISTS "direcao" direcao_nota DEFAULT 'recebida',
ADD COLUMN IF NOT EXISTS "emitente_nome" text,
ADD COLUMN IF NOT EXISTS "destinatario_nome" text,
ADD COLUMN IF NOT EXISTS "cfop" text,
ADD COLUMN IF NOT EXISTS "status_manifestacao" varchar DEFAULT 'pendente',
ADD COLUMN IF NOT EXISTS "processing" boolean DEFAULT false;

-- Enhance indexing for concurrent IDEMPOTENCY locks no Worker Node
-- (A combinação de empresa_id e chave_acesso deve ser única)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_notas_fiscais_empresa_chave_unique'
    ) THEN
        CREATE UNIQUE INDEX "idx_notas_fiscais_empresa_chave_unique" ON "notas_fiscais" ("empresa_id", "chave_acesso", "created_at");
    END IF;
END$$;
