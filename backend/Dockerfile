FROM python:3.11-slim

WORKDIR /app

# Install runtime + build libs needed by lxml/cryptography/xmlsec
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 libxml2-dev libxslt1.1 libxmlsec1-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements (uses pre-built wheels)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
