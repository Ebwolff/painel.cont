import sys
import os

# Garantir que a pasta local seja detectada
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app

# Este arquivo serve como o novo ponto de entrada (entry point) para a Vercel.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
