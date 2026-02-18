import sys
import os
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# 1. Configuração de Path Extremamente Primordial
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def create_emergency_app(error_msg: str, trace: str):
    app = FastAPI()
    
    @app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    async def catch_all_api(request: Request, path_name: str):
        # Verifica variáveis sem expor os valores REAIS
        keys_to_check = [
            "VITE_SUPABASE_URL", "SUPABASE_URL",
            "VITE_SUPABASE_ANON_KEY", "SUPABASE_KEY",
            "VITE_SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_SERVICE_ROLE_KEY",
            "VITE_MASTER_ENCRYPTION_KEY", "MASTER_ENCRYPTION_KEY"
        ]
        env_status = {k: "DEFINIDA" if os.environ.get(k) else "AUSENTE" for k in keys_to_check}
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "emergency_diagnostic_mode",
                "request_path": f"/api/{path_name}",
                "error": error_msg,
                "trace": trace,
                "env_check": env_status,
                "sys_path": sys.path,
                "current_dir": os.getcwd(),
                "tip": "Se você caiu aqui, o backend falhou ao importar o app principal. Verifique orequirements.txt e as chaves acima."
            }
        )
    return app

# 2. Tentativa de Importação com Diagnóstico Passo a Passo
try:
    print(f"DEBUG: Tentando importar app de {current_dir}")
    from app.main import app
    print("DEBUG: App importado com sucesso!")
except Exception as e:
    error_trace = traceback.format_exc()
    print(f"CRITICAL ERROR durante importação: {e}\n{error_trace}")
    # Se falhar, criamos o roteador de pânico que pega QUALQUER rota de API
    app = create_emergency_app(str(e), error_trace)

# A variável 'app' é exposta para a Vercel
