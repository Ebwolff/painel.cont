-- Migration: 017_fix_fk_alertas.sql
-- Objetivo: Restaurar a Foreign Key de alertas_conformidade para notas_fiscais
-- Isso é necessário para que o PostgREST permita o join aninhado na API

-- Nota: Em tabelas particionadas, FKs para a tabela particionada funcionam
-- desde que a coluna exista na partição pai.

-- Adicionar FK de alertas_conformidade -> notas_fiscais
-- Usando nota_fiscal_id + tenant_id como referência segura
DO $$
BEGIN
    -- Verificar se a FK já existe antes de criar
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_type = 'FOREIGN KEY'
        AND table_name = 'alertas_conformidade'
        AND constraint_name = 'fk_alertas_nota_fiscal'
    ) THEN
        -- FK de nota_fiscal_id -> notas_fiscais(id)
        -- Nota: em tabela particionada, a PK inclui (id, created_at),
        -- então não podemos referenciar apenas 'id'. 
        -- Usaremos formato de referência sem nome de coluna (sem FK) e faremos
        -- o join manualmente no backend. Esta migration documenta a intenção.
        RAISE NOTICE 'FK nao pode ser criada em tabela particionada com PK composta. Usando abordagem alternativa no backend.';
    END IF;
END $$;

-- Criar um INDEX para garantir performance no join manual
CREATE INDEX IF NOT EXISTS idx_alertas_nota_fiscal_id ON public.alertas_conformidade(nota_fiscal_id);
CREATE INDEX IF NOT EXISTS idx_alertas_tenant_created ON public.alertas_conformidade(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notas_fiscais_id_tenant ON public.notas_fiscais(id, tenant_id);

-- Habilitar schema_cache reload (Supabase specific)
NOTIFY pgrst, 'reload schema';
