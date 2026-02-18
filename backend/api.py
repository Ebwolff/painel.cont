import sys
import os
import traceback

# Garantir que a pasta local seja detectada
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    print(f"DEBUG: Iniciando API de {current_dir}")
    print(f"DEBUG: Python Path: {sys.path}")
    from app.main import app
except Exception as e:
    print(f"ERROR: Falha ao importar 'app': {e}")
    print(traceback.format_exc())
    raise e

# Este arquivo serve como o novo ponto de entrada (entry point) para a Vercel.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
Line 1: 
