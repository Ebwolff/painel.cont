-- Tabela sync_jobs: observabilidade de sincronizações SEFAZ
-- Cada chamada ao sync cria um registro para rastreamento.

CREATE TABLE IF NOT EXISTS sync_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    status TEXT NOT NULL DEFAULT 'queued',  -- queued, running, success, error, cooldown
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    duration_ms INT,
    notas_processadas INT DEFAULT 0,
    notas_manifestadas INT DEFAULT 0,
    notas_completas INT DEFAULT 0,
    notas_com_erro INT DEFAULT 0,
    novo_nsu TEXT,
    error_message TEXT,
    triggered_by TEXT DEFAULT 'manual',  -- manual, scheduled, webhook
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Índices para consultas comuns
CREATE INDEX IF NOT EXISTS idx_sync_jobs_empresa ON sync_jobs (empresa_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_tenant ON sync_jobs (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sync_jobs_status ON sync_jobs (status) WHERE status IN ('queued', 'running');

-- RLS: cada tenant vê apenas seus jobs
ALTER TABLE sync_jobs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS tenant_isolation_sync_jobs ON sync_jobs;
CREATE POLICY tenant_isolation_sync_jobs ON sync_jobs
  FOR ALL
  USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid)
  WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);
