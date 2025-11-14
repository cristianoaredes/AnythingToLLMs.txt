"""
Ponto de entrada da API REST do Anything to LLMs.txt.
"""

import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routers import converter, analyzer
from src.utils.logging_config import setup_logger
from src.api.services.conversion_service import redis_client

# Configurar logger
logger = setup_logger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Anything to LLMs.txt API",
    description="API para converter documentos em formato estruturado para uso com LLMs",
    version="1.0.0",
)

# Configurar CORS - Seguro por padrão
# Use CORS_ORIGINS env var para produção: "https://app.exemplo.com,https://admin.exemplo.com"
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Apenas métodos necessários
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],  # Apenas headers necessários
)

# Incluir routers
app.include_router(converter.router, prefix="/v1")
app.include_router(analyzer.router, prefix="/v1")

@app.get("/")
async def root():
    return {
        "message": "Bem-vindo à API do Anything to LLMs.txt",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log completo do erro (com stack trace para debug)
    logger.error(f"Erro não tratado: {str(exc)}", exc_info=True)

    # Em desenvolvimento, mostra detalhes; em produção, mensagem genérica
    is_dev = os.getenv("ENVIRONMENT", "production").lower() == "development"

    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc) if is_dev else "Erro interno do servidor. Por favor, tente novamente mais tarde.",
            "type": type(exc).__name__ if is_dev else "InternalServerError"
        }
    )

@app.on_event("shutdown")
async def shutdown_redis():
    await redis_client.close()

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
