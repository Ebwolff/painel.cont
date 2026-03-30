-- Migration: 015_add_tax_bases.sql
-- Adiciona colunas para armazenar as Bases de Cálculo (vBC) de cada imposto no detalhamento dos itens

-- 1. Alterar a Tabela nfe_items
ALTER TABLE public.nfe_items 
ADD COLUMN IF NOT EXISTS vbc_icms numeric(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS vbc_ipi numeric(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS vbc_pis numeric(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS vbc_cofins numeric(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS vbc_cbs numeric(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS vbc_ibs numeric(15,2) DEFAULT 0;

-- 2. Adicionar as bases correspondentes também ao cabeçalho (opcional para consolidação)
ALTER TABLE public.notas_fiscais
ADD COLUMN IF NOT EXISTS vbc_cbs numeric(15,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS vbc_ibs numeric(15,2) DEFAULT 0;
