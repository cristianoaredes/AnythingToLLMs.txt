"""
Ponto de entrada da API REST do Anything to LLMs.txt.
"""

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

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja para domínios autorizados
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor. Por favor, tente novamente mais tarde."}
    )

@app.on_event("shutdown")
async def shutdown_redis():
    await redis_client.close()

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
