-- Migrate: 002_evolucao_fiscal.sql

-- 1. Tabela de Regras Fiscais (O "Cérebro" do Sistema)
create table if not exists fiscal_rules (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  active boolean default true,
  severity text default 'media', -- 'baixa' | 'media' | 'alta'
  rule_type text not null, -- 'cbs', 'ibs', 'pis', 'cofins', 'icms'
  ncm text, -- NCM específico (opcional)
  cfop text, -- CFOP específico (opcional)
  cst text, -- CST específico (opcional)
  expected_rate numeric(5,4) not null,
  parameters jsonb default '{}'::jsonb, -- Parâmetros extras (ex: teto de valor)
  version text default '1.0.0',
  created_at timestamptz default now()
);

-- 2. Tabela de Itens da NF-e (Detalhamento Granular)
create table if not exists nfe_items (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  nota_fiscal_id uuid references notas_fiscais(id) on delete cascade,
  n_item integer,
  ncm text,
  cfop text,
  cst text,
  v_prod numeric(15,2),
  v_cbs numeric(15,2),
  v_ibs numeric(15,2),
  cbs_correto boolean,
  ibs_correto boolean,
  created_at timestamptz default now()
);

-- 3. Tabela de Scores de Exposição Fiscal (Histórico Mensal)
create table if not exists fiscal_scores (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  empresa_id uuid references empresas(id) on delete cascade,
  period text not null, -- Formato 'YYYY-MM'
  score numeric(5,2) not null, -- 0 a 100
  total_exposure numeric(15,2) default 0,
  total_inconsistencies integer default 0,
  created_at timestamptz default now(),
  unique(empresa_id, period)
);

-- 4. Tabela de Gestão de Alertas (Workflow de Resolução)
create table if not exists alerts_management (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  empresa_id uuid references empresas(id) on delete cascade,
  nfe_id uuid references notas_fiscais(id) on delete cascade,
  rule_id uuid references fiscal_rules(id) on delete set null,
  original_alert_id uuid references alertas_conformidade(id) on delete set null,
  status text default 'open', -- 'open' | 'analyzing' | 'resolved'
  assigned_to uuid references profiles(id), -- Referência a perfis de sistema (auth.users via profiles)
  resolution_comment text,
  created_at timestamptz default now(),
  resolved_at timestamptz
);

-- 5. Habilitar Segurança (RLS)
alter table fiscal_rules enable row level security;
alter table nfe_items enable row level security;
alter table fiscal_scores enable row level security;
alter table alerts_management enable row level security;

-- 6. Políticas de Acesso
-- Regras Fiscais: Todos os tenants podem ler as regras padrão
create policy "Tenants can view active rules" on fiscal_rules
  for select using (active = true);

-- Itens da NF-e
create policy "Tenant isolation for nfe_items" on nfe_items
  for all using (tenant_id = (select tenant_id from profiles where id = auth.uid()));

-- Scores
create policy "Tenant isolation for fiscal_scores" on fiscal_scores
  for all using (tenant_id = (select tenant_id from profiles where id = auth.uid()));

-- Gestão de Alertas
create policy "Tenant isolation for alerts_mgmt" on alerts_management
  for all using (tenant_id = (select tenant_id from profiles where id = auth.uid()));

-- 7. Garantir que a função de tenant_id automático existe
create or replace function public.handle_tenant_insert()
returns trigger as $$
begin
  if new.tenant_id is null then
    new.tenant_id := (select tenant_id from public.profiles where id = auth.uid());
  end if;
  return new;
end;
$$ language plpgsql security definer;

-- 8. Triggers para Preenchimento Automático de tenant_id
create trigger tr_nfe_item_tenant
  before insert on nfe_items
  for each row execute procedure handle_tenant_insert();

create trigger tr_fiscal_score_tenant
  before insert on fiscal_scores
  for each row execute procedure handle_tenant_insert();

create trigger tr_alerts_mgmt_tenant
  before insert on alerts_management
  for each row execute procedure handle_tenant_insert();
