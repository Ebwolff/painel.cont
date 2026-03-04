# Plano de Produção — SEFAZ NFeDistribuicaoDFe (SaaS Multi-Tenant)

> Stack: Python 3.12 + FastAPI + requests + lxml  
> Estado atual: mTLS funcional, 50 docs recebidos, `resNFe` parseado  
> Data: 04/03/2026

---

## Status das Melhorias

| # | Melhoria | Prioridade | Status |
|---|---------|:----------:|:------:|
| 1 | Content-Type SOAP 1.2 | 🔴 Alta | ✅ Deployado |
| 2 | cUFAutor dinâmico | 🔴 Alta | ✅ Deployado |
| 3 | Backoff erro 656 | 🔴 Alta | 📋 Proposto |
| 4 | Eliminar tmpfiles cert/key | 🟡 Média | 📋 Proposto |
| 5 | Validar expiração pré-sync | 🟡 Média | 📋 Proposto |
| 6 | Forçar TLS 1.2 mínimo | 🟢 Baixa | 📋 Proposto |
| 7 | Isolamento multi-tenant | 🔴 Alta | ✅ Existente (RLS) |
| 8 | Fila de sincronização | 🔴 Alta | 📋 Proposto |
| 9 | Service Layer isolada | 🟡 Média | 📋 Proposto |
| 10 | Manifestação automática | 🟡 Média | 📋 Proposto (adicional) |
| 11 | Observabilidade e métricas | 🟢 Baixa | 📋 Proposto (adicional) |

---

## MELHORIAS OBRIGATÓRIAS

---

### ✅ 1. Content-Type SOAP 1.2 — JÁ DEPLOYADO

Corrigido de `text/xml` para `application/soap+xml; charset=utf-8`. SOAPAction movido para parâmetro `action` do Content-Type conforme W3C SOAP 1.2, Part 2, §7.

---

### ✅ 2. cUFAutor dinâmico — JÁ DEPLOYADO

UF agora lida da tabela `empresas` com mapeamento IBGE completo (27 estados). Fallback para "35" (SP).

---

### 📋 3. Backoff inteligente para erro 656

**Risco atual:** Cada chamada rejeitada com 656 reinicia o cooldown de 1h da SEFAZ. Múltiplas empresas tentando sync simultaneamente podem causar bloqueio cascata.

**Solução — Controle por empresa com exponential backoff:**

#### [MODIFY] sefaz_sync.py

Adicionar verificação de cooldown antes de chamar a SEFAZ:

```python
from datetime import datetime, timezone, timedelta

COOLDOWN_MINUTES = 65  # 1h + margem de 5min

async def sync_company_documents(self, empresa_id, tenant_id):
    admin_client = self.supabase.get_service_client()
    
    # Checar cooldown ANTES de chamar SEFAZ
    cert_res = admin_client.table("certificados_a1") \
        .select("ultimo_sync, status") \
        .eq("empresa_id", empresa_id) \
        .maybe_single().execute()
    
    if cert_res.data:
        status = cert_res.data.get("status", "")
        ultimo_sync = cert_res.data.get("ultimo_sync")
        
        # Se status contém "656", checar se cooldown já expirou
        if "656" in status and ultimo_sync:
            last = datetime.fromisoformat(ultimo_sync)
            elapsed = datetime.now(timezone.utc) - last
            if elapsed < timedelta(minutes=COOLDOWN_MINUTES):
                remaining = COOLDOWN_MINUTES - int(elapsed.total_seconds() / 60)
                return {
                    "status": "cooldown",
                    "message": f"SEFAZ em cooldown. Tente novamente em {remaining} minutos.",
                    "retry_after_minutes": remaining,
                }
    
    # ... restante do sync
```

#### [MODIFY] sefaz_client.py

No `_parse_response`, identificar o 656 e propagar:

```python
if cstat == "656":
    logger.warning(f"SEFAZ: Consumo Indevido (656) — {xmot}")
    raise RuntimeError(f"SEFAZ 656: {xmot}")
```

**Impacto:** Previne requisições desnecessárias à SEFAZ e economiza recursos do certificado.

---

## MELHORIAS DE SEGURANÇA

---

### 📋 4. Eliminar arquivos temporários para cert/key

**Risco atual:** `sefaz_client.py:L104-L110` grava cert PEM e private key em disco como arquivos temporários. Em containers compartilhados, outro processo pode ler esses arquivos antes da limpeza.

**Solução — `requests_pkcs12`:**

```bash
pip install requests-pkcs12
```

#### [MODIFY] sefaz_client.py

```python
from requests_pkcs12 import post as pkcs12_post

def call_sefaz(self, pfx_bytes, password, cnpj, ultimo_nsu, codigo_uf):
    soap_body = self.build_soap_envelope(cnpj, ultimo_nsu, codigo_uf)
    headers = {
        "Content-Type": f'application/soap+xml; charset=utf-8; action="{SOAP_ACTION}"',
    }
    
    # mTLS direto em memória — ZERO arquivos em disco
    response = pkcs12_post(
        self.endpoint,
        data=soap_body.encode("utf-8"),
        headers=headers,
        pkcs12_data=pfx_bytes,
        pkcs12_password=password,
        verify=True,
        timeout=self.timeout,
    )
    response.raise_for_status()
    return self._parse_response(response.content)
```

**Impacto:** Elimina completamente a superfície de ataque de arquivos temporários. Remove ~20 linhas de código (tmpfile + unlink + try/finally).

---

### 📋 5. Validar expiração do certificado antes do sync

**Risco atual:** Certificado vencido causa `SSLError` genérico, sem mensagem amigável ao usuário.

#### [MODIFY] sefaz_sync.py

Adicionar a seleção de `vencimento` e checar antes de chamar:

```python
cert_res = admin_client.table("certificados_a1") \
    .select("certificado_enc, senha_enc, ultimo_nsu, ambiente, vencimento") \
    .eq("empresa_id", empresa_id) \
    .eq("status", "ativo") \
    .maybe_single().execute()

# Checar vencimento
vencimento_str = cert_row.get("vencimento")
if vencimento_str:
    vencimento = datetime.fromisoformat(vencimento_str)
    if vencimento < datetime.now(timezone.utc):
        admin_client.table("certificados_a1").update(
            {"status": "vencido"}
        ).eq("empresa_id", empresa_id).execute()
        return {
            "status": "error",
            "message": f"Certificado venceu em {vencimento.strftime('%d/%m/%Y')}. Faça upload de um novo certificado.",
        }
    
    dias_restantes = (vencimento - datetime.now(timezone.utc)).days
    if dias_restantes < 30:
        logger.warning(f"SEFAZ SYNC: Certificado vence em {dias_restantes} dias!")
        # Futuro: inserir alerta no sistema de notificações
```

**Impacto:** Evita chamadas inúteis à SEFAZ e dá feedback claro ao contador.

---

### 📋 6. Forçar TLS 1.2 mínimo

**Risco atual:** Baixo (Railway usa OpenSSL 3.x), mas compliance exige garantia explícita.

```python
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class TLS12Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.maximum_version = ssl.TLSVersion.TLSv1_3
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)
```

> **NOTA:** Se optar por `requests_pkcs12` (item 4), ele já permite passar `ssl_context` diretamente. Ambas as soluções são compatíveis.

---

## MELHORIAS ARQUITETURAIS (SaaS)

---

### 📋 7. Isolamento multi-tenant

**Estado atual: ✅ já implementado** via RLS no Supabase.

A tabela `certificados_a1` tem `tenant_id` e todas as queries filtram por `empresa_id` (que pertence a um tenant). A tabela `notas_fiscais` tem RLS ativo com policy baseada em `auth.uid() → profiles.tenant_id`.

**Recomendação adicional:** Garantir que a coluna `tenant_id` de `certificados_a1` seja restritiva na RLS:

```sql
CREATE POLICY "tenant_isolation_certs" ON certificados_a1
  USING (tenant_id = (SELECT tenant_id FROM profiles WHERE id = auth.uid()));
```

---

### 📋 8. Fila de sincronização

**Risco atual:** O endpoint `POST /sefaz/trigger/{empresa_id}` usa `BackgroundTasks` do FastAPI. Problemas:

| Problema | Impacto |
|----------|---------|
| Sem deduplicação | Usuário clica 5x → 5 syncs simultâneos |
| Sem persistência | Se o worker cair, a task é perdida |
| Sem rate limiting | 100 empresas sync ao mesmo tempo → SEFAZ bloqueia |
| Sem visibilidade | Usuário não sabe se terminou |

**Solução — Fila com controle de concorrência:**

#### Opção A: Lock no banco (simples, sem infra extra)

```python
# sefaz_sync.py - No início do sync
lock_res = admin_client.table("certificados_a1") \
    .update({"status": "sincronizando"}) \
    .eq("empresa_id", empresa_id) \
    .eq("status", "ativo") \
    .execute()

if not lock_res.data:
    return {"status": "already_running", "message": "Sincronização já em andamento."}

try:
    # ... executar sync
finally:
    # Garantir que o status volta para ativo
    admin_client.table("certificados_a1") \
        .update({"status": "ativo"}) \
        .eq("empresa_id", empresa_id) \
        .execute()
```

#### Opção B: Worker dedicado com ARQ (Redis-based, escalável)

```bash
pip install arq
```

```python
# worker.py
from arq import create_pool
from arq.connections import RedisSettings

async def sync_sefaz_job(ctx, empresa_id: str, tenant_id: str):
    service = SefazSyncService()
    return await service.sync_company_documents(empresa_id, tenant_id)

class WorkerSettings:
    functions = [sync_sefaz_job]
    redis_settings = RedisSettings(host="redis")
    max_jobs = 3  # máximo 3 syncs simultâneos
    job_timeout = 120
```

**Recomendação:** Começar com **Opção A** (lock no banco). Migrar para **Opção B** quando atingir >50 empresas.

---

### 📋 9. Service Layer isolada

**Risco atual:** `SefazSyncService` mistura orquestração (buscar cert, chamar SEFAZ, salvar) com lógica de negócio (validar, parsear).

**Proposta de separação:**

```
services/
├── sefaz/
│   ├── __init__.py
│   ├── client.py          # SefazClient (HTTP/SOAP) ← já existe
│   ├── sync_orchestrator.py  # Orquestra o fluxo completo
│   ├── document_processor.py # Parseia e salva docs
│   └── models.py          # Dataclasses tipadas
```

```python
# models.py
from dataclasses import dataclass

@dataclass
class SefazDocument:
    nsu: str
    chave_acesso: str | None
    xml_content: bytes
    tipo: str
    schema: str
    is_resumo: bool = False

@dataclass
class SyncResult:
    status: str  # "success" | "error" | "cooldown"
    notas_processadas: int = 0
    notas_com_erro: int = 0
    novo_nsu: str = ""
    message: str = ""
```

**Impacto:** Facilita testes unitários (mock do `SefazClient`), permite migração futura para APIs de terceiros (ex: Arquivei, FocusNFe) sem reescrever o orquestrador.

---

### 📋 10. Manifestação automática de resNFe (Adicional)

**Contexto:** A SEFAZ só envia o XML completo (`procNFe`) após a empresa manifestar ciência da nota. O `resNFe` é apenas o resumo.

**Fluxo necessário:**

```
App → SEFAZ: distDFeInt (ultNSU=X)
SEFAZ → App: 50x resNFe (resumos)
App: Salva resumos no banco
Loop para cada resNFe:
    App → SEFAZ: nfeRecepcaoEvento (ciência da operação, tipo 210210)
    SEFAZ → App: Evento registrado
App → SEFAZ: distDFeInt (ultNSU=Y)
SEFAZ → App: procNFe completos (XMLs inteiros)
```

**Implementação:** Criar novo método `manifest_documents()` no `SefazClient` que envia o evento tipo "210210" (Ciência da Operação) para cada chave de acesso recebida como `resNFe`.

> **IMPORTANTE:** Sem manifestação, a empresa nunca receberá o XML completo das notas. Isso é **obrigatório** para compliance fiscal.

---

### 📋 11. Observabilidade e métricas (Adicional)

**Proposta:** Tabela `sync_jobs` para rastrear cada execução:

```sql
CREATE TABLE sync_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    empresa_id UUID REFERENCES empresas(id),
    status TEXT DEFAULT 'running', -- running | success | error | cooldown
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    notas_processadas INT DEFAULT 0,
    notas_com_erro INT DEFAULT 0,
    ultimo_nsu TEXT,
    error_message TEXT,
    duration_ms INT
);
```

**Impacto:** Permite dashboard de monitoramento, debugging histórico, e SLA tracking.

---

## Roadmap de Implementação

### Fase 1 — Estabilidade (Esta semana)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 3 | Backoff erro 656 | 30 min | `sefaz_sync.py`, `sefaz_client.py` |
| 5 | Validar expiração cert | 15 min | `sefaz_sync.py` |
| 8A | Lock no banco (dedup) | 20 min | `sefaz_sync.py` |

### Fase 2 — Segurança (Próxima semana)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 4 | requests_pkcs12 | 30 min | `sefaz_client.py`, `requirements.txt` |
| 6 | TLS 1.2 enforcement | 10 min | `sefaz_client.py` |
| 7 | RLS cert table | 10 min | SQL migration |

### Fase 3 — Funcionalidade (Semana 3)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 10 | Manifestação resNFe | 3h | `sefaz_client.py` (novo método), `sefaz_sync.py` |
| 11 | Tabela sync_jobs | 1h | SQL migration, `sefaz_sync.py` |

### Fase 4 — Escala (Quando >50 empresas)

| # | Tarefa | Esforço | Arquivos |
|---|--------|---------|----------|
| 8B | Worker ARQ/Redis | 2h | Novo `worker.py`, Redis setup |
| 9 | Service Layer refactor | 2h | Reestruturação de diretórios |

---

> **Decisão necessária:** Deseja que eu comece pela **Fase 1** (backoff 656 + validação de vencimento + lock de deduplicação)?
