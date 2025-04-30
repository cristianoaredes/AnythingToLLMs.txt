# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Instala dependências de sistema para suportar Playwright
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl wget gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxss1 \
       libxcomposite1 libxrandr2 libgbm-dev libasound2 libpangocairo-1.0-0 \
       libgtk-3-0 libwoff1 libharfbuzz0b libjpeg-dev libxcb1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps

COPY . .

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"] 