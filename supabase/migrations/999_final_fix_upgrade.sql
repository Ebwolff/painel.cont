-- SCRIPT DE CORREÇÃO FINAL - SaaS END
-- Execute este script no SQL Editor do seu Supabase para resolver os erros 500.

-- 1. Criar a tabela de solicitações de plano (se não existir)
create table if not exists public.plan_requests (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    requested_plan text not null, -- 'pro', 'enterprise'
    status text not null default 'pending', -- 'pending', 'approved', 'rejected'
    created_at timestamptz default now(),
    processed_at timestamptz,
    admin_notes text
);

-- 2. Adicionar coluna de permissões em profiles (necessário para o admin gerenciar usuários)
alter table public.profiles add column if not exists permissions jsonb default '{}'::jsonb;

-- 3. Habilitar RLS e criar políticas básicas para plan_requests
alter table public.plan_requests enable row level security;

drop policy if exists "Users can view own tenant plan requests" on public.plan_requests;
create policy "Users can view own tenant plan requests" 
on public.plan_requests for select
using (tenant_id = (select tenant_id from profiles where id = auth.uid()));

drop policy if exists "Users can create plan requests" on public.plan_requests;
create policy "Users can create plan requests" 
on public.plan_requests for insert
with check (tenant_id = (select tenant_id from profiles where id = auth.uid()));

drop policy if exists "Super admins can manage all plan requests" on public.plan_requests;
create policy "Super admins can manage all plan requests"
on public.plan_requests for all
using (
    (select role from profiles where id = auth.uid()) = 'super_admin'
);

-- 4. Índices para performance
create index if not exists idx_plan_requests_status on public.plan_requests(status);
create index if not exists idx_plan_requests_tenant on public.plan_requests(tenant_id);

-- 5. Garantir que a coluna 'plano' em tenants está correta (Já está, mas por segurança)
-- alter table tenants rename column plan to plano; -- Apenas se já existisse 'plan'
