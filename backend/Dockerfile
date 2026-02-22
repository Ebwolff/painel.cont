# Usar uma imagem base leve com Python 3.10
FROM python:3.10-slim

# Evitar que o Python gere arquivos .pyc e permitir logs em tempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências de sistema necessárias para lxml e outras libs C
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    zlib1g-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar o cache de camadas do Docker
COPY requirements.txt .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do backend
COPY . .

# Expor a porta que o FastAPI usa
EXPOSE 8000

# Comando padrão para rodar a API (pode ser sobrescrito no docker-compose para o worker)
CMD ["uvicorn", "app_v5.main:app", "--host", "0.0.0.0", "--port", "8000"]
