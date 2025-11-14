"""
Serviço de conversão de documentos para a API REST.
"""

import os
import asyncio
import uuid
import time
import re
import json
from typing import Dict, List, Any, Optional, Tuple
import aiofiles
from src.tools.document_converter import DocumentConverterTool
from src.tools.token_analyzer import TokenAnalyzer
from src.tools.token_counter import count_tokens
from src.api.models import ConversionRequest, ConversionResult
from src.utils.logging_config import setup_logger
from src.config import REDIS_URL, UPLOAD_DIR, JOB_TTL_PROCESSING, JOB_TTL_COMPLETED, JOB_TTL_FAILED
from src.api.metrics import record_job_created, record_job_completed, record_job_failed
from redis.asyncio import Redis

# Configurar logger
logger = setup_logger(__name__)

# Inicializar cliente Redis para jobs
redis_client = Redis.from_url(REDIS_URL, decode_responses=True)

# Criar diretório de uploads
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_upload_file(file_content: bytes, filename: str) -> str:
    """Salva o arquivo enviado pelo usuário no diretório temporário."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(file_content)
    
    return file_path


async def process_document(
    job_id: str,
    file_path: str,
    params: ConversionRequest
) -> None:
    """
    Processa o documento de forma assíncrona em background.
    """
    try:
        job_key = f"job:{job_id}"
        # Atualizar status inicial em Redis
        await redis_client.hset(job_key, mapping={"status": "processing", "progress": "0.1"})
        
        # Inicializar conversor
        converter = DocumentConverterTool(
            chunk_size=params.chunk_size,
            chunk_overlap=params.chunk_overlap
        )
        
        # Lista de formatos de saída
        formats = [fmt.value for fmt in params.output_formats]
        
        # Medir tempo
        start_time = time.time()
        
        # Atualizar progresso
        await redis_client.hset(job_key, mapping={"progress": "0.2", "status_message": "Inicializando processamento"})
        
        # Processar documento (esta parte ainda é síncrona, mas rodará em uma thread separada)
        # Usamos run_in_executor para não bloquear a thread principal
        await redis_client.hset(job_key, mapping={"status_message": "Convertendo documento"})
        resultado = await asyncio.to_thread(
            converter.run,
            file_path=file_path,
            save_output=False,  # Não salvar em arquivo, retornar apenas
            profile=params.profile.value,
            ocr_engine=params.ocr_engine.value,
            ocr_language=params.ocr_language,
            force_ocr=params.force_ocr,
            export_formats=formats
        )
        
        await redis_client.hset(job_key, mapping={"progress": "0.7", "status_message": "Analisando documento"})
        
        # Extrair formatos resultantes
        formats_dict = resultado["formats"]
        
        # Calcular tempo total
        elapsed = time.time() - start_time
        
        # Contar tokens (apenas para o formato llms)
        token_count = None
        if "llms" in formats_dict:
            token_count = count_tokens(formats_dict["llms"], params.model_name)
            await redis_client.hset(job_key, mapping={"progress": "0.8"})
        
        # Análise de tokens
        analysis = None
        if token_count and params.profile.value == "llms-full":
            analyzer = TokenAnalyzer(params.model_name)
            # Extrair seções para análise
            llms_text = formats_dict["llms"]
            sections = re.split(r'(^# .+)', llms_text, flags=re.MULTILINE)
            section_map = {}
            current = None
            for part in sections:
                if part.strip().startswith('# '):
                    current = part.strip()
                    section_map[current] = ''
                elif current:
                    section_map[current] += part
            
            # Contar tokens por seção
            section_tokens = {sec: count_tokens(txt, params.model_name) for sec, txt in section_map.items()}
            
            # Analisar
            analysis = analyzer.analyze_sections(section_tokens)
            await redis_client.hset(job_key, mapping={"progress": "0.9"})
        
        # Exportação para frameworks (opcional)
        if params.to_langchain:
            await redis_client.hset(job_key, mapping={"status_message": "Exportando para framework LangChain"})
            doc = resultado["doc"]

            try:
                langchain_docs = converter.exportar_para_langchain(doc)
                if langchain_docs:
                    await redis_client.hset(job_key, mapping={"langchain_docs_count": len(langchain_docs)})
            except NotImplementedError as e:
                logger.warning(f"LangChain não implementado: {str(e)}")
                await redis_client.hset(job_key, mapping={
                    "langchain_error": "Funcionalidade não implementada",
                    "langchain_message": str(e)
                })
            except Exception as e:
                logger.error(f"Erro ao exportar para LangChain: {str(e)}")
                await redis_client.hset(job_key, mapping={"langchain_error": str(e)})

            await redis_client.hset(job_key, mapping={"progress": "0.95"})
        
        # Criar resultado e persistir em Redis
        result_data = {
            "formats": formats_dict,
            "token_count": token_count,
            "analysis": analysis,
            "processing_time": elapsed
        }
        await redis_client.hset(job_key, mapping={
            "status": "completed",
            "progress": "1.0",
            "status_message": "Processamento concluído",
            "result": json.dumps(result_data)
        })

        # Estender TTL após conclusão (para usuário buscar resultado)
        await redis_client.expire(job_key, JOB_TTL_COMPLETED)

        # Registrar métrica de sucesso
        record_job_completed(elapsed)

        # Limpar arquivo temporário após o processamento
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Falha ao remover arquivo temporário {file_path}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Erro no processamento do job {job_id}: {str(e)}")
        await redis_client.hset(job_key, mapping={"status": "failed", "error": str(e)})

        # Registrar métrica de falha
        record_job_failed()

        # TTL para jobs com erro (para debug)
        await redis_client.expire(job_key, JOB_TTL_FAILED)
        
        # Garantir limpeza mesmo em caso de erro
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass


async def create_conversion_job(
    file_content: bytes,
    filename: str,
    params: ConversionRequest
) -> str:
    """
    Cria um novo job de conversão e inicia o processamento em background.
    
    Args:
        file_content: Conteúdo do arquivo
        filename: Nome do arquivo
        params: Parâmetros de conversão
        
    Returns:
        job_id: ID do job criado
    """
    # Gerar ID único para o job
    job_id = str(uuid.uuid4())
    
    # Persistir metadados iniciais no Redis
    job_key = f"job:{job_id}"
    job_meta = {
        "status": "created",
        "progress": "0",
        "status_message": "Job criado",
        "created_at": str(time.time()),
        "filename": filename,
        "params": json.dumps(params.model_dump())
    }
    await redis_client.hset(job_key, mapping=job_meta)

    # Registrar métrica de job criado
    record_job_created()

    # TTL Strategy: Diferente para cada estado do job
    # TTL inicial (jobs em processamento que travaram)
    await redis_client.expire(job_key, JOB_TTL_PROCESSING)

    # Salvar arquivo
    file_path = await save_upload_file(file_content, f"{job_id}_{filename}")
    
    # Iniciar processamento em background
    asyncio.create_task(process_document(job_id, file_path, params))
    
    return job_id


async def get_job_status(job_id: str) -> Tuple[str, Optional[float], Optional[ConversionResult], Optional[str]]:
    """
    Obtém o status atual de um job.
    
    Args:
        job_id: ID do job
        
    Returns:
        status: Status do job (created, processing, completed, failed)
        progress: Progresso do processamento (0-1)
        result: Resultado se completo
        error: Mensagem de erro se falhou
    """
    # Ler do Redis
    job_key = f"job:{job_id}"
    exists = await redis_client.exists(job_key)
    if not exists:
        return "not_found", None, None, "Job não encontrado"
    job = await redis_client.hgetall(job_key)
    status = job.get("status")
    progress = float(job.get("progress")) if job.get("progress") else None
    error = job.get("error")
    result = None
    if job.get("result"):
        try:
            result_data = json.loads(job.get("result"))
            result = ConversionResult(**result_data)
        except:
            result = None
    return status, progress, result, error


async def get_job_details(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Obtém detalhes completos de um job do Redis.
    """
    job_key = f"job:{job_id}"
    exists = await redis_client.exists(job_key)
    if not exists:
        return None
    job = await redis_client.hgetall(job_key)
    # Converter tipos
    if job.get("progress"):
        job["progress"] = float(job["progress"])
    if job.get("created_at"):
        job["created_at"] = float(job["created_at"])
    if job.get("result"):
        try:
            job["result"] = json.loads(job["result"])
        except:
            pass
    return job


def cleanup_old_jobs() -> None:
    """Remove jobs antigos para evitar consumo excessivo de memória."""
    # Com Redis e TTL, limpeza automática não é necessária
    return
