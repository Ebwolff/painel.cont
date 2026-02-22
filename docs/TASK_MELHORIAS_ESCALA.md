# 📋 Task Board — Melhorias de Escala | END Monitor

**Última atualização:** 22/02/2026  
**Referência:** [AUDIT_ARCHITECTURE.md](./AUDIT_ARCHITECTURE.md) | [SCALE_VIABILITY_ANALYSIS.md](./SCALE_VIABILITY_ANALYSIS.md)

---

## 🔴 FASE 1 — Estabilização (0-500 clientes) | URGENTE

> Estimativa: ~1 semana de trabalho. Resolve 80% dos problemas para os próximos 6 meses.

### Bugs Críticos

- [x] **Fix bug double `file.read()` no `upload.py`** — 22/02/2026
  - Arquivo: `backend/app_v5/routers/upload.py` (linhas 29 e 51)
  - Status: ✅ Resolvido. Reusando variável `content`.

### Banco de Dados

- [x] **Criar migration com índices compostos** — 22/02/2026
  - Arquivo: `supabase/migrations/013_performance_indexes.sql`
  - Status: ✅ Criado migration com 10+ índices otimizados.
    - [ ] `idx_notas_tenant_created` (notas_fiscais: tenant_id, created_at DESC)
    - [ ] `idx_notas_tenant_status` (notas_fiscais: tenant_id, status)
    - [ ] `idx_notas_empresa_status` (notas_fiscais: empresa_id, status)
    - [ ] `idx_alertas_tenant_resolvido` (alertas_conformidade: tenant_id, resolvido)
    - [ ] `idx_alertas_empresa_resolvido` (alertas_conformidade: empresa_id, resolvido)
    - [ ] `idx_alertas_nota` (alertas_conformidade: nota_fiscal_id)
    - [ ] `idx_items_nota` (nfe_items: nota_fiscal_id)
    - [ ] `idx_items_ncm` (nfe_items: ncm)
    - [ ] `idx_rules_active_type` (fiscal_rules: active, rule_type)
    - [ ] `idx_rules_ncm` (fiscal_rules: ncm)
  - Impacto: **10x performance em queries do dashboard**

- [x] **Materialized views para dashboard** — 22/02/2026
  - Arquivo: `supabase/migrations/014_dashboard_materialized_view.sql`
  - Status: ✅ Criadas views `mv_dashboard_stats` e `mv_alerts_stats` com funções de refresh.
  - Impacto: **5x performance no dashboard, 90% menos queries**

### Infraestrutura

- [x] **Remover APScheduler do `main.py`** — 22/02/2026
  - Status: ✅ APScheduler removido. Substituído por Vercel Cron Jobs via endpoint `/api/cron/sync-tax-rates`.
  - Configuração adicionada ao `vercel.json`.

### Observabilidade

- [x] **Integrar Sentry SDK** — 22/02/2026
  - Status: ✅ Sentry SDK integrado ao backend (FastAPI). Requer variável `SENTRY_DSN` no deploy.

- [x] **Substituir `print()` por logging estruturado** — 22/02/2026
  - Arquivos afetados: `dashboard.py`, `supabase_client.py`, `upload.py`, `alerts.py`, `roi.py`, `sefaz.py`, `anomalies.py`, `companies.py`, `features.py`, `items.py`, `simulation.py`, `certificates.py`
  - Status: ✅ Concluído. 100% dos `print()` críticos do backend foram migrados para `logger`.

### Testes

- [x] **Test coverage mínimo** — 22/02/2026
  - [x] Configurar pytest + pytest-mock no `requirements.txt`
  - [x] Unit tests para `XMLParserService` (`tests/test_xml_parser.py`)
  - [x] Unit tests para `RuleEngineService` (`tests/test_rule_engine.py`)
  - [x] Integration tests para endpoints básicos (`tests/test_integration.py`)
  - [x] Configurar GitHub Actions CI (`.github/workflows/backend-ci.yml`)
  - Status: ✅ Concluído. Pipeline de testes ativa e core logic protegida.

---

## 🟡 FASE 2 — Escala Controlada (500-5.000 clientes) | 6-18 meses

> Requer mudança de infraestrutura. Planejar quando atingir ~200 clientes pagantes.

### Processamento Assíncrono

- [ ] **Implementar fila para processamento XML** — 16h
  - Opções: SQS (AWS) / BullMQ (Redis) / Celery
  - Upload recebe XML → envia para fila → worker processa em background
  - Response imediato ao usuário com status "processando"
  - Impacto: **Elimina timeout em uploads, permite escala horizontal de processing**

- [ ] **Background worker para fila XML** — 16h
  - Worker separado que consome da fila e processa notas
  - Retry automático com exponential backoff
  - Dead Letter Queue para falhas persistentes

### Cache

- [ ] **Implementar Redis para cache de dashboard** — 8h
  - ElastiCache ou Redis Cloud
  - TTL por tipo de dado: dashboard=5min, regras=1h, sessão=24h
  - Impacto: **90% menos queries ao banco**

- [ ] **Cache de `fiscal_rules` no Redis** — 4h
  - Atualmente: cache in-memory por instância (inútil em serverless)
  - Migrar para Redis com TTL de 1h e invalidação por evento
  - Impacto: **Elimina query de regras a cada request**

### Banco de Dados

- [ ] **Particionamento de tabelas por trimestre** — 8h
  - `notas_fiscais` → partition by RANGE(created_at)
  - `alertas_conformidade` → partition by RANGE(created_at)
  - `nfe_items` → partition by RANGE(created_at) — por mês (maior volume)
  - Impacto: **Queries históricas 10x mais rápidas**

- [ ] **Materialized view atualizada por trigger** — 8h
  - View se atualiza automaticamente quando novas notas são inseridas
  - Dashboard lê da view em vez de recalcular

### Infraestrutura

- [ ] **Migrar backend para processo persistente** — 4h
  - Railway, Render ou AWS ECS Fargate
  - Permite: workers, filas, scheduler, WebSockets
  - Impacto: **Desbloqueia todas as features de Fase 2**

- [ ] **Supabase Pooler (PgBouncer)** — 1h
  - Ativar connection pooling no Supabase
  - Impacto: **Escala de 500 para 5.000+ conexões sem novo banco**

- [ ] **Docker + CI/CD** — 8h
  - Dockerfile para backend
  - GitHub Actions: lint → test → build → deploy
  - Impacto: **Deploy profissional e reproduzível**

### Segurança

- [ ] **Auditar todos os usos de `service_client`** — 4h
  - Verificar que TODOS os endpoints com `get_service_client()` filtram por `tenant_id`
  - Risco: Se um filtro for omitido, dados de todos os tenants ficam expostos

- [ ] **Cache de sessão/token** — 4h
  - Atualmente: `supabase.auth.get_user(token)` é chamado a cada request (~100ms)
  - Cachear resultado no Redis com TTL de 5min

---

## 🔵 FASE 3 — Escala Nacional (5.000-50.000 clientes) | 18-36 meses

> Requer microserviços, time SRE, compliance enterprise.

### Arquitetura

- [ ] **Separar serviços: API / Upload / Reports** — 40h
  - API Gateway → serviço de leitura (dashboard, relatórios)
  - Upload Service → processamento de XML com fila
  - Report Service → geração de PDFs e exports
  - Escala independente por serviço

- [ ] **Kubernetes (EKS/GKE) com auto-scaling** — 24h
  - HPA (Horizontal Pod Autoscaler) baseado em CPU/memória
  - Node auto-scaling para picos

### Banco de Dados

- [ ] **Aurora PostgreSQL Multi-AZ** — 8h
  - Writer + 2-3 Read Replicas
  - Failover automático (<30s)
  - Impacto: **99,9% disponibilidade**

- [ ] **Sharding inicial por tenant ranges** — 24h
  - Preparação para Fase 4

### Compliance

- [ ] **SOC 2 Type II preparation** — 80h
- [ ] **LGPD compliance completo** — 40h
  - DPO nomeado
  - Criptografia em repouso
  - Anonimização de dados
  - Política de retenção

### Produto

- [ ] **API pública com SDK** — 40h
  - Integração com ERPs e sistemas contábeis
  - Canal de distribuição

- [ ] **Pentest externo** — 16h
  - Contratação de empresa especializada
  - Resultado documentado para investidores

---

## 🟣 FASE 4 — Escala Massiva (50.000-100.000+) | 36+ meses

> Requer Série A/B, time de 20-40 pessoas, infra multi-região.

### Infraestrutura

- [ ] **Kubernetes Multi-Region** — 80h
- [ ] **Aurora Global Database** — 40h
- [ ] **Redis Cluster geo-replicado** — 16h
- [ ] **CloudFront + Lambda@Edge** — 8h

### Dados

- [ ] **Database sharding por tenant group** — 80h
- [ ] **Event sourcing (Kafka/Kinesis)** — 40h
- [ ] **Data Lake: S3 + Glue + Athena** — 24h

### Produto Enterprise

- [ ] **SSO (SAML/OIDC)** — 24h
- [ ] **ML para detecção de anomalias fiscais** — 80h
- [ ] **Marketplace de regras fiscais** — 40h
- [ ] **White-label para contabilidades enterprise** — 80h

---

## ✅ JÁ CONCLUÍDO

- [x] **Fix `apscheduler` no `requirements.txt`** — 22/02/2026
  - Causa raiz da tela preta na Vercel: pacote faltando fazia backend entrar em modo de emergência
  - Commit: `0242ead`

- [x] **Resilência do `Dashboard.tsx`** — 20/02/2026
  - Checks defensivos para dados de API (Array.isArray, optional chaining)
  - Fallback para dados ausentes/formato inesperado

- [x] **Memoização do `useFeatures.ts`** — 20/02/2026
  - `useCallback` para `hasFeature` e `isTier`
  - `useMemo` para `features`
  - Fix do loop infinito de re-renders

- [x] **Interface `Alert` alinhada** — 20/02/2026
  - Adição de `mensagem` opcional na interface
  - Fix do erro TypeScript TS2339

- [x] **Proteção XXE no XMLParser** — Já implementado
  - `resolve_entities=False`, `no_network=True`, `load_dtd=False`

- [x] **Criptografia Fernet (AES-128)** — Já implementado
  - Dados sensíveis criptografados em repouso

- [x] **RLS Multi-Tenant** — Já implementado
  - Row Level Security em todas as tabelas com policies por tenant

- [x] **Audit Log** — Já implementado
  - `log_audit()` em `SupabaseService` para ações sensíveis

- [x] **Rate Limiting** — Já implementado
  - `slowapi` configurado no `main.py`

- [x] **Documento AUDIT_ARCHITECTURE.md** — 22/02/2026
  - Commit: `53ae9db`

- [x] **Documento SCALE_VIABILITY_ANALYSIS.md** — 22/02/2026
  - Commit: `b834c18`

---

> **Como usar:** Marque `[x]` conforme cada item for concluído e adicione a data.
> Atualize a seção "JÁ CONCLUÍDO" movendo os itens com data e commit.
