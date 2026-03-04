# SEFAZ Integration — Task Tracker

> Início: 04/03/2026 | Estimativa total: ~10h

---

## Itens já concluídos (pré-plano)

- [x] Corrigir envelope SOAP (`<nfeDistDFeInteresse>` wrapper)
- [x] Content-Type → `application/soap+xml` (SOAP 1.2)
- [x] Remover header SOAPAction (movido para Content-Type)
- [x] cUFAutor dinâmico (lido da tabela `empresas`, mapeamento IBGE 27 UFs)
- [x] Parser `resNFe` — aceitar resumos da SEFAZ sem crash
- [x] `sefaz_sync.py` — skip validação/itens para resumos
- [x] Error handler captura XML de erro SEFAZ (HTTP 500 body)

---

## Fase 1 — Estabilidade (~1h)

- [ ] Backoff erro 656 (Consumo Indevido)
  - [ ] Detectar cStat 656 no `_parse_response` e lançar RuntimeError
  - [ ] Checar cooldown (65min) antes de chamar SEFAZ
  - [ ] Salvar status "656" no banco para controle temporal
- [ ] Validar expiração do certificado antes do sync
  - [ ] Adicionar `vencimento` na query do certificado
  - [ ] Bloquear sync se vencido, atualizar status → "vencido"
  - [ ] Log warning se vence em < 30 dias
- [ ] Lock de deduplicação (anti-double-click)
  - [ ] Status "sincronizando" antes do sync
  - [ ] Rejeitar sync se já está em andamento
  - [ ] Garantir status volta a "ativo" no `finally`

---

## Fase 2 — Manifestação do Destinatário (~6h30) ⭐ CRÍTICA

### 2a. Infraestrutura

- [ ] `sefaz_endpoints.py` (NOVO)
  - [ ] `get_codigo_ibge_uf(uf)` — mapeamento 27 UFs
  - [ ] `gerar_id_lote()` — UUID truncado 15 dígitos
  - [ ] `get_dist_dfe_url(uf, ambiente)` — endpoint distDFe (AN)
  - [ ] `get_recepcao_evento_url(uf, ambiente)` — 9 próprios + SVRS
  - [ ] Endpoints produção + homologação

### 2b. Assinatura Digital

- [ ] `xml_signer.py` (NOVO)
  - [ ] Classe `XMLSigner` com perfis sha1/sha256
  - [ ] Método `sign_event()` — Enveloped Signature, C14N Exclusive
  - [ ] Carregar cert/key do PFX em memória
  - [ ] Instalar `xmlsec` no `requirements.txt`
  - [ ] Configurar `libxmlsec1-dev` no `nixpacks.toml`

### 2c. Método manifest_document()

- [ ] Montar XML `envEvento` v1.00
  - [ ] `cOrgao` dinâmico via `get_codigo_ibge_uf()`
  - [ ] `idLote` via `gerar_id_lote()` (UUID)
  - [ ] Event ID = `ID` + tpEvento(6) + chNFe(44) + nSeqEvento(02)
  - [ ] Suporte 4 tipos: 210200, 210210, 210220, 210240
- [ ] Assinar com `XMLSigner`
- [ ] Envelope SOAP 1.2 para `RecepcaoEvento4`
- [ ] Enviar via `requests_pkcs12` (mTLS em memória)
- [ ] `_parse_evento_response()` — extrair cStat, xMotivo, nProt

### 2d. Migração SQL

- [ ] `019_manifestacao.sql`
  - [ ] Campos: `manifestado`, `tipo_manifestacao`, `protocolo_evento`, `data_manifestacao`, `n_seq_evento`, `is_resumo`
  - [ ] Índice parcial para consulta de pendentes
  - [ ] Executar migração no Supabase

### 2e. Orquestrador 4 Etapas

- [ ] ETAPA 1: `distDFeInt` → salvar resNFe com `is_resumo=true`
- [ ] ETAPA 2: Manifestar pendentes (máx 20 por ciclo)
  - [ ] Rate limiting: `asyncio.sleep(0.5)` entre chamadas
  - [ ] Break imediato em cStat 656
  - [ ] Salvar protocolo em 135, 136, 573
  - [ ] Tratar 580 (fora de prazo) e 217 (não consta)
- [ ] ETAPA 3: Redistribuição pós-manifestação
  - [ ] Nova chamada `distDFeInt` se `manifestadas > 0`
  - [ ] Processar `procNFe` completos
  - [ ] Atualizar nota existente (resumo → completa)
  - [ ] Inserir itens da nota
- [ ] ETAPA 4: Atualizar `ultimo_nsu` + `ultimo_sync`

### 2f. Instalar dependências

- [ ] `pip install xmlsec requests-pkcs12`
- [ ] `nixpacks.toml` → `aptPkgs = ["libxmlsec1-dev", "pkg-config"]`

### 2g. Testes Unitários

- [ ] `test_corgao_dinamico`
- [ ] `test_id_lote_uniqueness`
- [ ] `test_build_evento_xml`
- [ ] `test_sign_sha1`
- [ ] `test_sign_sha256`
- [ ] `test_event_id_format`
- [ ] `test_endpoint_all_27_ufs`
- [ ] `test_dist_dfe_is_national`
- [ ] `test_idempotency_573`
- [ ] `test_protocol_saved_136`
- [ ] `test_cooldown_656_breaks`
- [ ] `test_rate_limit_delay`
- [ ] `test_redistribuicao_cycle`

---

## Fase 3 — Segurança (~50min)

- [ ] Eliminar tmpfiles cert/key
  - [ ] Substituir por `requests_pkcs12` (mTLS em memória)
  - [ ] Remover blocos `tempfile` + `unlink`
- [ ] Forçar TLS 1.2 mínimo
  - [ ] Criar `TLS12Adapter` ou usar `ssl_context` do pkcs12
- [ ] RLS na tabela `certificados_a1`
  - [ ] Policy `tenant_isolation_certs`

---

## Fase 4 — Escala (quando >50 empresas, ~4h)

- [ ] Worker ARQ/Redis para fila de sync
- [ ] Service Layer refactor (separar orquestração de negócio)
- [ ] Tabela `sync_jobs` (observabilidade)

---

## Deploy Final

- [ ] Commit + push de todas as mudanças
- [ ] Verificar deploy Railway
- [ ] Teste end-to-end: upload cert → sync → manifestação → procNFe
