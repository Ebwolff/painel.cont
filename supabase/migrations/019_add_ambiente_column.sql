-- Migration 019: Adicionar coluna 'ambiente' à tabela certificados_a1
-- A tabela foi criada antes da migration 018 incluir esta coluna.
-- Este ALTER é idempotente (IF NOT EXISTS).

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'certificados_a1'
        AND column_name = 'ambiente'
    ) THEN
        ALTER TABLE certificados_a1
        ADD COLUMN ambiente TEXT DEFAULT 'producao';
        RAISE NOTICE 'Coluna ambiente adicionada com sucesso.';
    ELSE
        RAISE NOTICE 'Coluna ambiente já existe. Nenhuma alteração necessária.';
    END IF;
END $$;
