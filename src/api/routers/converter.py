"""
Rotas para conversão de documentos.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
import json
from src.api.models import ConversionRequest, ConversionResponse, StatusResponse
from src.api.services.conversion_service import create_conversion_job, get_job_status, get_job_details
from src.utils.logging_config import setup_logger
from src.api.dependencies import verify_api_key, rate_limiter
from src.api.services.url_fetcher import fetch_and_save_url
from src.config import MAX_FILE_SIZE, SUPPORTED_FORMATS
import os

# Configurar logger
logger = setup_logger(__name__)

router = APIRouter(
    prefix="/convert",
    tags=["convert"],
    dependencies=[Depends(verify_api_key), Depends(rate_limiter)]
)

@router.post("/", response_model=ConversionResponse)
async def convert_document(
    file: UploadFile = File(None),
    url: str = Form(None),
    params: str = Form(default="{}")
):
    """
    Converte um documento para o formato LLMs.txt e outros formatos solicitados.
    
    - **file**: Arquivo a ser convertido (PDF, DOCX, HTML, etc.)
    - **url**: URL do documento a ser convertido
    - **params**: Parâmetros de conversão em formato JSON
    """
    # Deve enviar arquivo ou URL, não ambos
    if not file and not url:
        raise HTTPException(status_code=400, detail="Você deve fornecer um arquivo ou uma URL")
    if file and url:
        raise HTTPException(status_code=400, detail="Envie apenas um arquivo ou uma URL, não ambos")

    # Obter conteúdo e nome do arquivo
    if url:
        temp_path = None
        try:
            temp_path = await fetch_and_save_url(url)
            file_content = open(temp_path, 'rb').read()
            filename = os.path.basename(temp_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Falha ao obter URL: {str(e)}")
        finally:
            # Limpar arquivo temporário
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Não foi possível deletar arquivo temporário {temp_path}: {str(e)}")
    else:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Arquivo não fornecido")
        file_content = await file.read()
        filename = file.filename
    
    # Verificar extensão do arquivo
    file_ext = filename.split('.')[-1].lower()

    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato de arquivo não suportado. Formatos suportados: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Verificar tamanho do arquivo
    if len(file_content) > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"Tamanho máximo de arquivo excedido ({max_mb:.0f}MB)"
        )
    
    # Processar parâmetros
    try:
        # Parse dos parâmetros JSON
        params_dict = json.loads(params)
        params_obj = ConversionRequest(**params_dict)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Parâmetros JSON inválidos")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro nos parâmetros: {str(e)}")
    
    # Criar job de conversão
    job_id = await create_conversion_job(file_content, filename, params_obj)
    
    return ConversionResponse(job_id=job_id, status="processing")


@router.get("/{job_id}", response_model=StatusResponse)
async def get_conversion_status(job_id: str):
    """
    Obtém o status de um job de conversão.
    
    - **job_id**: ID do job retornado pela rota de conversão
    """
    status, progress, result, error = await get_job_status(job_id)
    
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    response = StatusResponse(
        job_id=job_id,
        status=status,
        progress=progress,
        result=result,
        error=error
    )
    
    return response


@router.get("/{job_id}/details")
async def get_job_details_route(job_id: str):
    """
    Obtém detalhes adicionais de um job, incluindo status, progresso e mensagens.
    
    - **job_id**: ID do job retornado pela rota de conversão
    """
    details = await get_job_details(job_id)
    
    if details is None:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    # Remover items muito grandes para a resposta JSON
    if "result" in details and details["result"] is not None:
        # Truncar formatos grandes para preview
        if "formats" in details["result"]:
            for fmt, content in details["result"]["formats"].items():
                if isinstance(content, str) and len(content) > 1000:
                    details["result"]["formats"][fmt] = content[:1000] + "... (truncado)"
    
    return details
