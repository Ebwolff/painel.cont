-- Migration 018: Garantir tabela certificados_a1 completa com coluna ultimo_nsu
-- O último NSU permite sincronização incremental: busca só documentos novos

CREATE TABLE IF NOT EXISTS certificados_a1 (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    empresa_id      UUID NOT NULL REFERENCES empresas(id) ON DELETE CASCADE,
    certificado_enc TEXT NOT NULL,       -- PFX criptografado (Fernet/AES)
    senha_enc       TEXT NOT NULL,       -- Senha criptografada
    vencimento      TIMESTAMPTZ,
    ultimo_nsu      TEXT DEFAULT '000000000000000', -- NSU do último doc recebido da SEFAZ
    ambiente        TEXT DEFAULT 'homologacao',     -- 'homologacao' | 'producao'
    status          TEXT DEFAULT 'ativo',           -- 'ativo' | 'vencido' | 'erro'
    ultimo_sync     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (empresa_id)  -- Uma empresa tem apenas um certificado ativo
);

-- Índice para busca por tenant
CREATE INDEX IF NOT EXISTS idx_cert_tenant ON certificados_a1 (tenant_id);
CREATE INDEX IF NOT EXISTS idx_cert_empresa ON certificados_a1 (empresa_id);

-- RLS: escritório só vê seus próprios certificados
ALTER TABLE certificados_a1 ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "tenant_cert_isolation" ON certificados_a1;
CREATE POLICY "tenant_cert_isolation" ON certificados_a1
    USING (tenant_id = (SELECT tenant_id FROM profiles WHERE id = auth.uid()));

-- Updated_at automático
CREATE OR REPLACE FUNCTION update_cert_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_cert_updated_at ON certificados_a1;
CREATE TRIGGER trg_cert_updated_at
    BEFORE UPDATE ON certificados_a1
    FOR EACH ROW EXECUTE FUNCTION update_cert_updated_at();
