-- Manifestação do Destinatário: campos adicionais na tabela notas_fiscais
-- Para rastrear status de manifestação e controle de idempotência.

ALTER TABLE notas_fiscais
  ADD COLUMN IF NOT EXISTS manifestado BOOLEAN DEFAULT false,
  ADD COLUMN IF NOT EXISTS tipo_manifestacao TEXT,
  ADD COLUMN IF NOT EXISTS protocolo_evento TEXT,
  ADD COLUMN IF NOT EXISTS data_manifestacao TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS n_seq_evento INT DEFAULT 1,
  ADD COLUMN IF NOT EXISTS is_resumo BOOLEAN DEFAULT false;

-- Índice parcial para consulta rápida de notas pendentes de manifestação
CREATE INDEX IF NOT EXISTS idx_notas_manifestacao_pendente
  ON notas_fiscais (empresa_id, manifestado)
  WHERE manifestado = false AND is_resumo = true;
