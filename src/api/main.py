"""
Ponto de entrada da API REST do Anything to LLMs.txt.
"""

import os
import shutil
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from src.api.routers import converter, analyzer
from src.utils.logging_config import setup_logger
from src.api.services.conversion_service import redis_client
from src.config import UPLOAD_DIR

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
    """
    Health check inteligente que verifica:
    - Status geral da API
    - Conexão com Redis
    - Espaço em disco disponível
    """
    health_status = {
        "status": "healthy",
        "checks": {}
    }

    # 1. Verificar Redis
    try:
        await redis_client.ping()
        health_status["checks"]["redis"] = {"status": "ok", "message": "Connected"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["redis"] = {"status": "error", "message": str(e)}

    # 2. Verificar espaço em disco
    try:
        disk_usage = shutil.disk_usage(UPLOAD_DIR)
        free_gb = disk_usage.free / (1024**3)
        total_gb = disk_usage.total / (1024**3)
        percent_used = (disk_usage.used / disk_usage.total) * 100

        if percent_used > 95:
            health_status["status"] = "unhealthy"
            disk_status = "critical"
        elif percent_used > 85:
            disk_status = "warning"
        else:
            disk_status = "ok"

        health_status["checks"]["disk"] = {
            "status": disk_status,
            "free_gb": round(free_gb, 2),
            "total_gb": round(total_gb, 2),
            "percent_used": round(percent_used, 1)
        }
    except Exception as e:
        health_status["checks"]["disk"] = {"status": "error", "message": str(e)}

    # 3. Verificar diretório de upload
    try:
        if os.path.exists(UPLOAD_DIR) and os.access(UPLOAD_DIR, os.W_OK):
            health_status["checks"]["upload_dir"] = {"status": "ok", "writable": True}
        else:
            health_status["status"] = "unhealthy"
            health_status["checks"]["upload_dir"] = {"status": "error", "writable": False}
    except Exception as e:
        health_status["checks"]["upload_dir"] = {"status": "error", "message": str(e)}

    # Retornar código HTTP apropriado
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(status_code=status_code, content=health_status)

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
