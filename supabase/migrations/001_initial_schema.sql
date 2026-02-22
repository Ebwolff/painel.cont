-- Migrate: 001_initial_schema.sql

-- 1. Create Tenants (Escritórios de Contabilidade)
create table if not exists tenants (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text unique not null,
  plano text default 'free',
  created_at timestamptz default now()
);

-- 2. Create Profiles (Extensão do auth.users)
create table if not exists profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  tenant_id uuid references tenants(id) on delete cascade,
  nome text not null,
  email text not null,
  role text default 'contador', -- 'admin' | 'contador'
  created_at timestamptz default now()
);

-- 3. Create Empresas (Clientes do Escritório)
create table if not exists empresas (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  razao_social text not null,
  cnpj text not null,
  regime_tributario text, -- 'simples' | 'lucro_presumido' | 'lucro_real'
  risco_score integer default 0, -- 0-100 (termômetro)
  total_notas integer default 0,
  notas_com_erro integer default 0,
  created_at timestamptz default now(),
  unique(tenant_id, cnpj)
);

-- 4. Create Notas Fiscais
create table if not exists notas_fiscais (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  empresa_id uuid references empresas(id) on delete cascade,
  chave_acesso text unique,
  numero text,
  serie text,
  tipo text, -- 'nfe' | 'nfse'
  emitente_cnpj text,
  destinatario_cnpj text,
  valor_total numeric(15,2),
  valor_cbs numeric(15,2),
  valor_ibs numeric(15,2),
  aliquota_cbs numeric(5,4),
  aliquota_ibs numeric(5,4),
  cbs_correto boolean,
  ibs_correto boolean,
  status text default 'pendente', -- 'pendente' | 'conforme' | 'irregular' | 'erro_parse'
  xml_url text,
  data_emissao timestamptz,
  processado_em timestamptz,
  created_at timestamptz default now()
);

-- 5. Create Alertas de Conformidade
create table if not exists alertas_conformidade (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid references tenants(id) on delete cascade,
  empresa_id uuid references empresas(id) on delete cascade,
  nota_fiscal_id uuid references notas_fiscais(id) on delete cascade,
  tipo text not null, -- 'cbs_incorreto' | 'ibs_incorreto' | 'cbs_ausente' | 'ibs_ausente'
  severidade text default 'alta', -- 'baixa' | 'media' | 'alta' | 'critica'
  mensagem text not null,
  valor_esperado numeric(15,2),
  valor_encontrado numeric(15,2),
  diferenca numeric(15,2),
  resolvido boolean default false,
  created_at timestamptz default now()
);

-- 6. Enable Row Level Security (RLS)
alter table tenants enable row level security;
alter table profiles enable row level security;
alter table empresas enable row level security;
alter table notas_fiscais enable row level security;
alter table alertas_conformidade enable row level security;

-- 7. Create RLS Policies (Multi-Tenancy Isolation)

-- Profiles: Usuário vê seu próprio perfil
create policy "Users can view own profile" on profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);

-- Para as outras tabelas, a regra é: tenant_id da linha deve ser igual ao tenant_id do usuário logado (armazenado no perfil)

-- Empresas
create policy "Tenant isolation for empresas" on empresas
  for all using (
    tenant_id = (select tenant_id from profiles where id = auth.uid())
  );

-- Notas Fiscais
create policy "Tenant isolation for notas_fiscais" on notas_fiscais
  for all using (
    tenant_id = (select tenant_id from profiles where id = auth.uid())
  );

-- Alertas
create policy "Tenant isolation for alertas" on alertas_conformidade
  for all using (
    tenant_id = (select tenant_id from profiles where id = auth.uid())
  );

-- 8. Triggers para atualizar automáticos (Opcional, mas recomendado)
-- Criar uma função para garantir que o tenant_id seja preenchido no insert baseado no perfil do usuário
create or replace function public.handle_tenant_insert()
returns trigger as $$
begin
  new.tenant_id := (select tenant_id from public.profiles where id = auth.uid());
  return new;
end;
$$ language plpgsql security definer;

-- Aplicar o trigger para garantir multi-tenancy no insert automático
create trigger on_empresa_insert
  before insert on empresas
  for each row execute procedure handle_tenant_insert();

create trigger on_nota_insert
  before insert on notas_fiscais
  for each row execute procedure handle_tenant_insert();

create trigger on_alerta_insert
  before insert on alertas_conformidade
  for each row execute procedure handle_tenant_insert();
