-- Migration: 016_table_partitioning.sql - v9 (Autolimpante e Idempotente)
-- Objetivo: Converter tabelas para particionamento, resolvendo erros de execução interrompida.

-- ⚠️ ESTE SCRIPT É AUTOLIMPANTE: Se houver restos de execuções anteriores, ele os remove.
BEGIN;

--------------------------------------------------------------------------------
-- 0. LIMPEZA PREVENTIVA
--------------------------------------------------------------------------------
-- Remove as tabelas novas (particionadas) caso existam de uma falha anterior.
-- Isso é seguro pois os dados originais estão nas tabelas '_old'.
DROP TABLE IF EXISTS public.notas_fiscais CASCADE;
DROP TABLE IF EXISTS public.alertas_conformidade CASCADE;
DROP TABLE IF EXISTS public.nfe_items CASCADE;

--------------------------------------------------------------------------------
-- 1. NOTAS FISCAIS
--------------------------------------------------------------------------------

-- Renomeia apenas se a '_old' ainda não existir. Se existir, usamos a que já está lá.
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'notas_fiscais' AND NOT tablename LIKE '%_old') 
       AND NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'notas_fiscais_old') THEN
        ALTER TABLE public.notas_fiscais RENAME TO notas_fiscais_old;
    END IF;
END $$;

-- Criar particionada (Cols confirmadas na v8)
CREATE TABLE public.notas_fiscais (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES public.tenants(id) ON DELETE CASCADE,
    empresa_id uuid REFERENCES public.empresas(id) ON DELETE CASCADE,
    chave_acesso text,
    numero text,
    serie text,
    emitente_cnpj text,
    emitente_nome text,
    destinatario_cnpj text,
    destinatario_nome text,
    valor_total numeric(15,2),
    valor_cbs numeric(15,2),
    valor_ibs numeric(15,2),
    cbs_correto boolean,
    ibs_correto boolean,
    status text DEFAULT 'pendente',
    xml_url text,
    data_emissao timestamptz,
    processado_em timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, created_at),
    UNIQUE (chave_acesso, created_at)
) PARTITION BY RANGE (created_at);

-- Partições 2026
CREATE TABLE IF NOT EXISTS notas_fiscais_y2026_q1 PARTITION OF notas_fiscais FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE IF NOT EXISTS notas_fiscais_y2026_q2 PARTITION OF notas_fiscais FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');
CREATE TABLE IF NOT EXISTS notas_fiscais_y2026_q3 PARTITION OF notas_fiscais FOR VALUES FROM ('2026-07-01') TO ('2026-10-01');
CREATE TABLE IF NOT EXISTS notas_fiscais_y2026_q4 PARTITION OF notas_fiscais FOR VALUES FROM ('2026-10-01') TO ('2027-01-01');

-- Migrar dados (SE existir a old)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'notas_fiscais_old') THEN
        INSERT INTO public.notas_fiscais (
            id, tenant_id, empresa_id, chave_acesso, numero, serie,
            emitente_cnpj, emitente_nome, destinatario_cnpj, destinatario_nome,
            valor_total, valor_cbs, valor_ibs, cbs_correto, ibs_correto, 
            status, xml_url, data_emissao, processado_em, created_at
        )
        SELECT
            src.id, src.tenant_id, src.empresa_id, src.chave_acesso, src.numero, src.serie,
            src.emitente_cnpj, COALESCE(src.emitente_nome, ''), src.destinatario_cnpj, COALESCE(src.destinatario_nome, ''),
            src.valor_total, src.valor_cbs, src.valor_ibs, src.cbs_correto, src.ibs_correto,
            src.status, src.xml_url, src.data_emissao, src.processado_em, src.created_at
        FROM public.notas_fiscais_old src
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

ALTER TABLE public.notas_fiscais ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant isolation for notas_fiscais" ON public.notas_fiscais FOR ALL USING (tenant_id = (select tenant_id from profiles where id = auth.uid()));
CREATE TRIGGER on_nota_insert BEFORE INSERT ON public.notas_fiscais FOR EACH ROW EXECUTE PROCEDURE public.handle_tenant_insert();

--------------------------------------------------------------------------------
-- 2. ALERTAS CONFORMIDADE
--------------------------------------------------------------------------------

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'alertas_conformidade' AND NOT tablename LIKE '%_old') 
       AND NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'alertas_conformidade_old') THEN
        ALTER TABLE public.alertas_conformidade RENAME TO alertas_conformidade_old;
    END IF;
END $$;

CREATE TABLE public.alertas_conformidade (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES public.tenants(id) ON DELETE CASCADE,
    empresa_id uuid REFERENCES public.empresas(id) ON DELETE CASCADE,
    nota_fiscal_id uuid,
    tipo text NOT NULL,
    severidade text DEFAULT 'alta',
    mensagem text NOT NULL,
    valor_esperado numeric(15,2),
    valor_encontrado numeric(15,2),
    diferenca numeric(15,2),
    resolvido boolean DEFAULT false,
    is_opportunity boolean DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE IF NOT EXISTS alertas_y2026_q1 PARTITION OF alertas_conformidade FOR VALUES FROM ('2026-01-01') TO ('2026-04-01');
CREATE TABLE IF NOT EXISTS alertas_y2026_q2 PARTITION OF alertas_conformidade FOR VALUES FROM ('2026-04-01') TO ('2026-07-01');

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'alertas_conformidade_old') THEN
        INSERT INTO public.alertas_conformidade (
            id, tenant_id, empresa_id, nota_fiscal_id, tipo, severidade, mensagem,
            valor_esperado, valor_encontrado, diferenca, resolvido, is_opportunity, created_at
        )
        SELECT
            a.id, a.tenant_id, a.empresa_id, a.nota_fiscal_id, a.tipo, a.severidade, a.mensagem,
            a.valor_esperado, a.valor_encontrado, a.diferenca, a.resolvido, a.is_opportunity, a.created_at
        FROM public.alertas_conformidade_old a
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

ALTER TABLE public.alertas_conformidade ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant isolation for alertas" ON public.alertas_conformidade FOR ALL USING (tenant_id = (select tenant_id from profiles where id = auth.uid()));
CREATE TRIGGER on_alerta_insert BEFORE INSERT ON public.alertas_conformidade FOR EACH ROW EXECUTE PROCEDURE public.handle_tenant_insert();

--------------------------------------------------------------------------------
-- 3. NFE ITEMS
--------------------------------------------------------------------------------

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'nfe_items' AND NOT tablename LIKE '%_old') 
       AND NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'nfe_items_old') THEN
        ALTER TABLE public.nfe_items RENAME TO nfe_items_old;
    END IF;
END $$;

CREATE TABLE public.nfe_items (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES public.tenants(id) ON DELETE CASCADE,
    nota_fiscal_id uuid,
    n_item integer,
    ncm text,
    cfop text,
    cst text,
    v_prod numeric(15,2),
    v_cbs numeric(15,2),
    v_ibs numeric(15,2),
    cbs_correto boolean,
    ibs_correto boolean,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

CREATE TABLE IF NOT EXISTS nfe_items_y2026_m01 PARTITION OF nfe_items FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE IF NOT EXISTS nfe_items_y2026_m02 PARTITION OF nfe_items FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

DO $$ 
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'nfe_items_old') THEN
        INSERT INTO public.nfe_items (
            id, tenant_id, nota_fiscal_id, n_item, ncm, cfop, cst,
            v_prod, v_cbs, v_ibs, cbs_correto, ibs_correto, created_at
        )
        SELECT
            i.id, i.tenant_id, i.nota_fiscal_id, i.n_item, i.ncm, i.cfop, i.cst,
            i.v_prod, i.v_cbs, i.v_ibs, i.cbs_correto, i.ibs_correto, i.created_at
        FROM public.nfe_items_old i
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

ALTER TABLE public.nfe_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Tenant isolation for nfe_items" ON public.nfe_items FOR ALL USING (tenant_id = (select tenant_id from profiles where id = auth.uid()));
CREATE TRIGGER tr_nfe_item_tenant BEFORE INSERT ON public.nfe_items FOR EACH ROW EXECUTE PROCEDURE public.handle_tenant_insert();

COMMIT;
