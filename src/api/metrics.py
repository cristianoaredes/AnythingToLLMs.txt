"""
Métricas Prometheus para monitoramento.

Exporta métricas no formato Prometheus em /metrics.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import Response as FastAPIResponse
import time


# ========================================
# Métricas
# ========================================

# Requisições HTTP
http_requests_total = Counter(
    'http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status']
)

# Duração de requisições
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Duração de requisições HTTP em segundos',
    ['method', 'endpoint']
)

# Requisições em andamento
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Número de requisições HTTP em andamento'
)

# Jobs de conversão
conversion_jobs_total = Counter(
    'conversion_jobs_total',
    'Total de jobs de conversão',
    ['status']  # created, completed, failed
)

conversion_job_duration_seconds = Histogram(
    'conversion_job_duration_seconds',
    'Duração de jobs de conversão em segundos'
)

# Erros
errors_total = Counter(
    'errors_total',
    'Total de erros',
    ['type', 'endpoint']
)

# Health checks
health_check_status = Gauge(
    'health_check_status',
    'Status do health check (1=healthy, 0=unhealthy)'
)

redis_connection_status = Gauge(
    'redis_connection_status',
    'Status da conexão com Redis (1=connected, 0=disconnected)'
)

disk_usage_percent = Gauge(
    'disk_usage_percent',
    'Percentual de uso de disco'
)


# ========================================
# Middleware
# ========================================

async def metrics_middleware(request: Request, call_next):
    """
    Middleware para capturar métricas de todas as requisições.
    """
    # Ignorar endpoint de métricas
    if request.url.path == "/metrics":
        return await call_next(request)

    # Incrementar requisições em andamento
    http_requests_in_progress.inc()

    # Medir tempo
    start_time = time.time()

    try:
        # Processar requisição
        response = await call_next(request)

        # Calcular duração
        duration = time.time() - start_time

        # Registrar métricas
        http_requests_total.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response

    except Exception as e:
        # Registrar erro
        errors_total.labels(
            type=type(e).__name__,
            endpoint=request.url.path
        ).inc()
        raise

    finally:
        # Decrementar requisições em andamento
        http_requests_in_progress.dec()


# ========================================
# Endpoint de Métricas
# ========================================

async def metrics_endpoint():
    """
    Endpoint que expõe métricas no formato Prometheus.

    Acesse em /metrics
    """
    return FastAPIResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# ========================================
# Funções auxiliares
# ========================================

def record_job_created():
    """Registra criação de job."""
    conversion_jobs_total.labels(status="created").inc()


def record_job_completed(duration: float):
    """Registra conclusão de job."""
    conversion_jobs_total.labels(status="completed").inc()
    conversion_job_duration_seconds.observe(duration)


def record_job_failed():
    """Registra falha de job."""
    conversion_jobs_total.labels(status="failed").inc()


def update_health_metrics(healthy: bool, redis_ok: bool, disk_percent: float):
    """Atualiza métricas de health check."""
    health_check_status.set(1 if healthy else 0)
    redis_connection_status.set(1 if redis_ok else 0)
    disk_usage_percent.set(disk_percent)
