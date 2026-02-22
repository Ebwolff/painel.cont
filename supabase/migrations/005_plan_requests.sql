-- Migrate: 005_plan_requests.sql
-- Tabela para gerenciar solicitações de upgrade de plano por parte dos escritórios.

create table if not exists public.plan_requests (
    id uuid primary key default gen_random_uuid(),
    tenant_id uuid not null references public.tenants(id) on delete cascade,
    requested_plan text not null, -- 'starter', 'pro', 'enterprise'
    status text not null default 'pending', -- 'pending', 'approved', 'rejected'
    created_at timestamptz default now(),
    processed_at timestamptz,
    admin_notes text
);

-- Segurança (RLS)
alter table public.plan_requests enable row level security;

-- Política: Usuário pode ver suas próprias solicitações de seu tenant
create policy "Users can view own tenant plan requests" 
on public.plan_requests for select
using (tenant_id = (select tenant_id from profiles where id = auth.uid()));

-- Política: Usuário pode criar solicitações para seu tenant
create policy "Users can create plan requests" 
on public.plan_requests for insert
with check (tenant_id = (select tenant_id from profiles where id = auth.uid()));

-- Política: Super Admin pode fazer TUDO (Bypass via Service Role ou política explícita se necessário)
-- Como o backend usa Service Role para operações admin, geralmente não precisamos de política explícita para o admin aqui,
-- mas é boa prática permitir select para o super_admin se ele usar o client autenticado.

create policy "Super admins can manage all plan requests"
on public.plan_requests for all
using (
    (select role from profiles where id = auth.uid()) = 'super_admin'
);

-- Índices para performance
create index if not exists idx_plan_requests_status on public.plan_requests(status);
create index if not exists idx_plan_requests_tenant on public.plan_requests(tenant_id);
