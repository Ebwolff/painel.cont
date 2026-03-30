# SEFAZ RPA Worker - XML Download Emissor

Worker escalável em Python + Playwright para automatizar o download de Notas Fiscais Eletrônicas (NF-e) diretamente do Portal Nacional da NF-e, contornando a restrição estrutural de Web Services para notas de Emissão Própria.

## 🚀 Como Funciona
O Worker opera conectando-se a uma fila Redis. Quando o backend SaaS precisa baixar uma NF-e de um cliente, ele publica um Job na fila contendo a `chave`, o `empresa_id`, e as credenciais temporárias do certificado A1 (`pfx_path`, `pfx_password`).

O Worker então:
1. Inicia um contexto Chromium invisível.
2. Injeta o certificado `.pfx` no nível do navegador.
3. Acessa o Portal Nacional.
4. Delega a resolução do hCaptcha para um serviço terceirizado (ex: 2Captcha).
5. Intercepta o download do arquivo `.xml`.
6. Salva localmente e dispara um Webhook para o Backend SaaS.

## 🛠 Passos para Executar

### 1. Preparar Ambiente
```bash
cd rpa_worker
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

### 2. Configuração (`.env`)
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```
Edite as variáveis cruciais:
* `REDIS_URL`: URL da sua fila Redis (Local ou Nuvem).
* `CAPTCHA_API_KEY`: API Key da sua conta no 2Captcha ou AntiCaptcha.
* `WEBHOOK_URL`: O endpoint no seu Node.js/NestJS que receberá o status do sucesso.
* `HEADLESS`: `true` para ambiente de produção (servidor linux), `false` para ver o robô agir em sua máquina local.

### 3. Rodando o Worker
Habilite o Redis Server e em seguida execute:
```bash
python main.py
```

### 4. Publicando um Job (Exemplo Node.js)
```typescript
import Redis from 'ioredis';
const redis = new Redis("redis://localhost:6379/0");

redis.rpush("nfe_download_queue", JSON.stringify({
    chave: "52251245453214002448550110003222441592263350",
    empresa_id: "uuid-da-empresa",
    pfx_path: "/diretorio/seguro/empresa_cert.pfx",
    pfx_password: "senha-segura-123"
}));
```

## 🧠 Arquitetura e Decisões
* **Segurança:** O certificado `.pfx` nunca trafega descriptografado nos logs e é descartado do contexto assim que o browser fecha. A injeção é nativa no Playwright `client_certificates`.
* **Idempotência:** A fila `blpop` assegura que múltiplos Workers (Escalonamento Horizontal) não peguem o mesmo Job simultaneamente.
* **Resiliência:** O `pydantic` assegura validação e há blocos de `try/except` nas transições do DOM. Retentativas (Max 3) são empregadas em caso de Timeout do site do governo.
