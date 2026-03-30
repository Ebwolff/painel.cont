-- Migration to support NFE Worker NestJS V2 Hybrid Sync

-- Create Enum type for TipoNota if it doesn't already exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_nota') THEN
        CREATE TYPE tipo_nota AS ENUM ('emitida', 'recebida');
    END IF;
END$$;

-- Add V2 structural columns to the existing notas_fiscais table
ALTER TABLE "notas_fiscais" 
ADD COLUMN IF NOT EXISTS "tipo" tipo_nota DEFAULT 'recebida',
ADD COLUMN IF NOT EXISTS "processing" boolean DEFAULT false;

-- Enhance indexing for concurrent IDEMPOTENCY locks on the Node Worker
-- (The combination of empresa_id and chave must be unique for safe lock release)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_indexes 
        WHERE indexname = 'idx_notas_fiscais_empresa_chave_unique'
    ) THEN
        CREATE UNIQUE INDEX "idx_notas_fiscais_empresa_chave_unique" ON "notas_fiscais" ("empresa_id", "chave");
    END IF;
END$$;
