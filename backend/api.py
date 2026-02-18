from app.main import app

# Este arquivo serve como o novo ponto de entrada (entry point) para a Vercel.
# Ele garante que o requirements.txt na raiz da pasta backend seja detectado.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
