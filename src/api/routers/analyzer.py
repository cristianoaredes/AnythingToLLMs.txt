"""
Rotas para análise de tokens.
"""

from fastapi import APIRouter, HTTPException, Depends
from src.api.models import TokenAnalysisRequest, TokenAnalysisResponse
from src.api.services.analyzer_service import analyze_token_usage
from src.utils.logging_config import setup_logger
from src.api.dependencies import verify_api_key, rate_limiter

# Configurar logger
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/analyzer",
    tags=["analyzer"],
    dependencies=[Depends(verify_api_key), Depends(rate_limiter)]
)


@router.post("/tokens", response_model=TokenAnalysisResponse)
async def analyze_tokens(request: TokenAnalysisRequest):
    """
    Analisa o uso de tokens em um texto.
    
    - **content**: Texto a ser analisado
    - **model_name**: Nome do modelo para contagem de tokens
    """
    if not request.content:
        raise HTTPException(status_code=400, detail="Conteúdo não fornecido")
    
    # Limitar tamanho do conteúdo (max 1MB)
    if len(request.content) > 1 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Tamanho máximo de conteúdo excedido (1MB)"
        )
    
    # Processar análise
    result = await analyze_token_usage(request.content, request.model_name)
    
    return TokenAnalysisResponse(**result)


@router.post("/detect-content-type")
async def detect_content_type(request: TokenAnalysisRequest):
    """
    Detecta o tipo de conteúdo de um texto e sugere configurações de chunking.
    
    - **content**: Texto a ser analisado
    - **model_name**: Nome do modelo para contagem de tokens (opcional)
    """
    if not request.content:
        raise HTTPException(status_code=400, detail="Conteúdo não fornecido")
    
    # Limitar tamanho do conteúdo (max 1MB)
    if len(request.content) > 1 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Tamanho máximo de conteúdo excedido (1MB)"
        )
    
    # Processar análise
    result = await analyze_token_usage(request.content, request.model_name)
    
    # Extrair tipo de conteúdo e recomendações de chunking
    response = {
        "content_type": result.get("content_type"),
        "chunking_recommendation": result.get("chunking_recommendation"),
        "total_tokens": result.get("total_tokens"),
        "model_name": result.get("model_name")
    }
    
    return response
