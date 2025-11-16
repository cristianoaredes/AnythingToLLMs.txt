# syntax=docker/dockerfile:1

# ========================================
# Stage 1: Builder - Instala dependências
# ========================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc g++ make \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas requirements primeiro (cache layer)
COPY requirements.txt .

# Instalar dependências Python em um diretório separado
RUN pip install --no-cache-dir --user -r requirements.txt

# ========================================
# Stage 2: Runtime - Imagem final mínima
# ========================================
FROM python:3.11-slim

# Labels para metadados
LABEL maintainer="Anything to LLMs.txt"
LABEL description="API para converter documentos em formato estruturado para LLMs"
LABEL version="1.0.0"

# Criar usuário não-root para segurança
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Instalar apenas dependências runtime (Playwright precisa de browsers)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       # Playwright dependencies
       curl wget \
       libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 \
       libxcomposite1 libxrandr2 libgbm-dev libasound2 libpangocairo-1.0-0 \
       libgtk-3-0 libwoff1 libharfbuzz0b libjpeg-dev libxcb1 \
       # OCR dependencies
       tesseract-ocr tesseract-ocr-por tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar dependências Python do builder
COPY --from=builder /root/.local /root/.local

# Adicionar ao PATH
ENV PATH=/root/.local/bin:$PATH

# Instalar browsers do Playwright (necessário mesmo após copiar)
RUN playwright install chromium --with-deps

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Criar diretórios necessários
RUN mkdir -p temp/uploads \
    && chown -R appuser:appuser temp

# Variáveis de ambiente padrão
ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    UPLOAD_DIR=/app/temp/uploads \
    LOG_FORMAT=json

# Expor porta
EXPOSE 8000

# Health check inteligente (usa o novo endpoint)
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Trocar para usuário não-root
USER appuser

# Comando de inicialização
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
