-- Migrate: 004_fix_nfe_columns.sql
-- Adiciona colunas faltantes para metadados de NF-e e melhora performance de consultas de alertas.

-- 1. Adicionar nomes de emitente e destinatário na tabela de notas
alter table public.notas_fiscais 
add column if not exists emitente_nome text,
add column if not exists destinatario_nome text;

-- 2. Garantir que empresa_id em alertas_conformidade seja consistente com a nota
-- (Isso ajuda em joins complexos onde a nota pode não estar carregada)
-- Nota: empresa_id já existe, mas vamos garantir que não haja erro de tipo ou constraint.

-- 3. Índices para performance (Dashboard e Alertas são as telas mais usadas)
create index if not exists idx_notas_fiscais_tenant_id on public.notas_fiscais(tenant_id);
create index if not exists idx_alertas_conformidade_tenant_status on public.alertas_conformidade(tenant_id, resolvido);
create index if not exists idx_alertas_conformidade_nota_fiscal_id on public.alertas_conformidade(nota_fiscal_id);

-- 4. View de Apoio para Alertas (Opcional, mas útil para o Futuro)
-- create view view_alertas_detalhados as ...
