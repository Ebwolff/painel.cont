from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="END Monitor Contábil API",
    description="API para monitoramento de conformidade tributária (Reforma 2026)",
    version="1.0.0"
)

# Rate Limiting Configuration
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
# Em produção, deve ser estrito.
allowed_origins_env = os.getenv("VITE_ALLOWED_ORIGINS") or os.getenv("ALLOWED_ORIGINS") or ""
origins = []
allow_all = False

if allowed_origins_env == "*":
    allow_all = True
    origins = ["*"]
elif allowed_origins_env:
    origins = allowed_origins_env.split(",")
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
    ]

# Nota: Se allow_origins for ["*"], allow_credentials não pode ser True.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=not allow_all, # Desabilita se for * para evitar erro de navegador
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import dashboard, upload, alerts, companies, roi, certificates, sefaz, admin, users, debug

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(debug.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(upload.router, prefix="/api/upload", tags=["Upload"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(roi.router, prefix="/api/roi", tags=["ROI"])
app.include_router(certificates.router, prefix="/api/certificates", tags=["Certificates"])
app.include_router(sefaz.router, prefix="/api/sefaz", tags=["SEFAZ"])
app.include_router(admin.router, prefix="/api") # Prefixo já incluído no router (/admin)
app.include_router(users.router, prefix="/api") # Prefixo já incluído (/users)

@app.get("/api/health")
async def health_check():
    return {
        "status": "active", 
        "system": "END Monitor Contábil", 
        "version": "1.0.0"
    }

@app.get("/api/debug-env")
async def debug_env():
    """Rota segura para verificar se as chaves estão presentes na Vercel."""
    keys_to_check = [
        "VITE_SUPABASE_URL", "SUPABASE_URL",
        "VITE_SUPABASE_ANON_KEY", "SUPABASE_KEY",
        "VITE_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY",
        "VITE_MASTER_ENCRYPTION_KEY", "MASTER_ENCRYPTION_KEY",
        "VITE_ALLOWED_ORIGINS", "ALLOWED_ORIGINS"
    ]
    env_status = {k: "DEFINIDA" if os.environ.get(k) else "AUSENTE" for k in keys_to_check}
    return {
        "status": "online",
        "env_check": env_status,
        "tip": "Se VITE_SUPABASE_URL for o endereço do seu site, o frontend vai dar erro 404 ao tentar falar com o banco."
    }

if __name__ == "__main__":
    import uvicorn
    # Em desenvolvimento usamos reload, em produção a Vercel/PaaS ignora esse bloco.
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
