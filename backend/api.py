import sys
import os
import traceback

# Diagnóstico de Ambiente
print(f"DEBUG: Python Version: {sys.version}")
print(f"DEBUG: Current Dir: {os.getcwd()}")
print(f"DEBUG: System Path: {sys.path}")

try:
    from app.main import app
    print("DEBUG: App imported successfully")
except Exception as e:
    print(f"CRITICAL: Failed to import app: {e}")
    print(traceback.format_exc())
    # Cria uma aplicação dummy para evitar crash de invocação e mostrar o erro na rota
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/api/dashboard/current-company")
    @app.get("/api/health")
    def error_route():
        return {"status": "error", "detail": str(e), "trace": traceback.format_exc()}

# Variável 'app' deve estar no escopo global para o handler da Vercel
