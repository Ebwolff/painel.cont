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

from app_v5.v5.routers import dashboard, upload, alerts, companies, roi, certificates, sefaz, admin, users, debug

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
    """Rota segura para verificar se as chaves estão presentes na Vercel e testar o banco."""
    from app_v5.v5.core.supabase_client import SupabaseService
    
    keys_to_check = [
        "VITE_SUPABASE_URL", "SUPABASE_URL",
        "VITE_SUPABASE_ANON_KEY", "SUPABASE_KEY",
        "VITE_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY",
        "VITE_MASTER_ENCRYPTION_KEY", "MASTER_ENCRYPTION_KEY",
        "VITE_ALLOWED_ORIGINS", "ALLOWED_ORIGINS"
    ]
    env_status = {k: "DEFINIDA" if os.environ.get(k) else "AUSENTE" for k in keys_to_check}
    
    db_status = "Não testado"
    db_counts = {}
    db_error = None
    
    try:
        supabase = SupabaseService()
        admin_client = supabase.get_service_client()
        
        # Teste 1: Contagem de Perfis
        profiles_res = admin_client.table("profiles").select("id", count="exact").limit(1).execute()
        db_counts["profiles"] = profiles_res.count
        
        # Teste 2: Contagem de Notas (opcional)
        try:
            notas_res = admin_client.table("notas_fiscais").select("id", count="exact").limit(1).execute()
            db_counts["notas_fiscais"] = notas_res.count
        except:
            db_counts["notas_fiscais"] = "erro ou tabela ausente"
            
        db_status = "Conexão OK"
    except Exception as e:
        db_status = "Falha na Conexão"
        db_error = str(e)
        
    return {
        "status": "online",
        "env_check": env_status,
        "db_test": {
            "version": "v5-bust",
            "status": db_status,
            "counts": db_counts,
            "error": db_error
        },
        "tip": "Se db_test.status for 'Falha', verifique a URL e a SERVICE_ROLE_KEY."
    }

if __name__ == "__main__":
    import uvicorn
    # Em desenvolvimento usamos reload, em produção a Vercel/PaaS ignora esse bloco.
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app_v5.main:app", host="0.0.0.0", port=port, reload=False)
