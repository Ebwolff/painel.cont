-- RLS para tabela certificados_a1
-- Garante que cada escritório só acessa seus próprios certificados.

ALTER TABLE certificados_a1 ENABLE ROW LEVEL SECURITY;

-- Remover policies existentes (se houver) para evitar duplicidade
DROP POLICY IF EXISTS tenant_isolation_certs ON certificados_a1;

-- Leitura: tenant só vê seus certificados
CREATE POLICY tenant_isolation_certs ON certificados_a1
  FOR ALL
  USING (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid)
  WITH CHECK (tenant_id = (auth.jwt() ->> 'tenant_id')::uuid);
