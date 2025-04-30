import os
import time
from fastapi import Header, HTTPException
from fastapi import Depends
from src.api.services.conversion_service import redis_client

# Carrega configuração de API key e rate limit (requests por minuto)
API_KEY = os.getenv("LLMS_API_KEY")
RATE_LIMIT = int(os.getenv("LLMS_RATE_LIMIT", "60"))

async def verify_api_key(x_api_key: str = Header(None)):
    """Verifica se o X-API-Key corresponde à chave configurada."""
    # Se não houver API_KEY configurada, não aplica autenticação
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

async def rate_limiter(x_api_key: str = Header(None)):
    """Aplica limitador de taxa baseado em Redis."""
    # Se não houver API_KEY configurada, não aplica rate limiting
    if not API_KEY:
        return
    # Verifica header
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    # Contador por minuto
    bucket_key = f"rl:{x_api_key}:{int(time.time()//60)}"
    count = await redis_client.incr(bucket_key)
    if count == 1:
        await redis_client.expire(bucket_key, 60)
    if count > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded") 