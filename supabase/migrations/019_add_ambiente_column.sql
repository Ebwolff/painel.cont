-- Migration 019: Garantir que TODAS as colunas esperadas pelo código existam
-- na tabela certificados_a1. Adiciona apenas as que estão faltando.

DO $$
BEGIN
    -- certificado_enc
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'certificado_enc') THEN
        ALTER TABLE certificados_a1 ADD COLUMN certificado_enc TEXT;
        RAISE NOTICE 'Coluna certificado_enc adicionada.';
    END IF;

    -- senha_enc
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'senha_enc') THEN
        ALTER TABLE certificados_a1 ADD COLUMN senha_enc TEXT;
        RAISE NOTICE 'Coluna senha_enc adicionada.';
    END IF;

    -- vencimento
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'vencimento') THEN
        ALTER TABLE certificados_a1 ADD COLUMN vencimento TIMESTAMPTZ;
        RAISE NOTICE 'Coluna vencimento adicionada.';
    END IF;

    -- ambiente
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'ambiente') THEN
        ALTER TABLE certificados_a1 ADD COLUMN ambiente TEXT DEFAULT 'producao';
        RAISE NOTICE 'Coluna ambiente adicionada.';
    END IF;

    -- status
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'status') THEN
        ALTER TABLE certificados_a1 ADD COLUMN status TEXT DEFAULT 'ativo';
        RAISE NOTICE 'Coluna status adicionada.';
    END IF;

    -- ultimo_nsu
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'ultimo_nsu') THEN
        ALTER TABLE certificados_a1 ADD COLUMN ultimo_nsu TEXT DEFAULT '000000000000000';
        RAISE NOTICE 'Coluna ultimo_nsu adicionada.';
    END IF;

    -- ultimo_sync
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'ultimo_sync') THEN
        ALTER TABLE certificados_a1 ADD COLUMN ultimo_sync TIMESTAMPTZ;
        RAISE NOTICE 'Coluna ultimo_sync adicionada.';
    END IF;

    -- tenant_id
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'tenant_id') THEN
        ALTER TABLE certificados_a1 ADD COLUMN tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
        RAISE NOTICE 'Coluna tenant_id adicionada.';
    END IF;

    -- empresa_id (unique constraint)
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'empresa_id') THEN
        ALTER TABLE certificados_a1 ADD COLUMN empresa_id UUID UNIQUE REFERENCES empresas(id) ON DELETE CASCADE;
        RAISE NOTICE 'Coluna empresa_id adicionada.';
    END IF;

    -- updated_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'updated_at') THEN
        ALTER TABLE certificados_a1 ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
        RAISE NOTICE 'Coluna updated_at adicionada.';
    END IF;

    -- created_at
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'certificados_a1' AND column_name = 'created_at') THEN
        ALTER TABLE certificados_a1 ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
        RAISE NOTICE 'Coluna created_at adicionada.';
    END IF;
END $$;
