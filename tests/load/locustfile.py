"""
Load testing para API com Locust.

Testa capacidade da API sob carga e identifica gargalos.

Uso:
    # Teste local
    locust -f tests/load/locustfile.py --host=http://localhost:8000

    # Teste headless
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

    # Web UI
    locust -f tests/load/locustfile.py --host=http://localhost:8000
    # Acesse: http://localhost:8089
"""
import os
import random
import time
from locust import HttpUser, task, between, events
from io import BytesIO


class LLMsAPIUser(HttpUser):
    """
    Simula um usuário da API.

    Comportamento:
    - Aguarda 1-3s entre requisições (simula usuário real)
    - Faz diferentes tipos de requisições (health, conversão, status)
    - Usa API key configurada
    """

    wait_time = between(1, 3)  # Aguardar 1-3s entre requisições

    def on_start(self):
        """Executado quando usuário inicia."""
        self.api_key = os.getenv("LLMS_API_KEY", "test-key-123")
        self.headers = {"X-API-Key": self.api_key}
        self.job_ids = []  # Armazena IDs de jobs criados

    @task(10)
    def health_check(self):
        """
        Task mais frequente: Health check (peso 10).

        Health check deve ser rápido (<100ms).
        """
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                # Verificar estrutura da resposta
                data = response.json()
                if "status" in data and "checks" in data:
                    response.success()
                else:
                    response.failure("Resposta de health check inválida")
            else:
                response.failure(f"Health check falhou: {response.status_code}")

    @task(5)
    def get_metrics(self):
        """
        Task moderada: Buscar métricas (peso 5).

        Prometheus metrics endpoint.
        """
        self.client.get("/metrics")

    @task(3)
    def root_endpoint(self):
        """Task leve: Endpoint raiz (peso 3)."""
        self.client.get("/")

    @task(2)
    def start_conversion_small_file(self):
        """
        Task pesada: Iniciar conversão de arquivo pequeno (peso 2).

        Simula upload de PDF pequeno.
        """
        # Criar PDF mínimo válido (224 bytes)
        pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000114 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n224\n%%EOF"

        files = {"file": ("test.pdf", BytesIO(pdf_content), "application/pdf")}
        data = {"params": '{"profile": "llms-min"}'}

        with self.client.post(
            "/v1/convert/",
            headers=self.headers,
            files=files,
            data=data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                job_data = response.json()
                if "job_id" in job_data:
                    self.job_ids.append(job_data["job_id"])
                    response.success()
                else:
                    response.failure("job_id não retornado")
            elif response.status_code == 401:
                response.failure("Autenticação falhou - verificar API key")
            else:
                response.failure(f"Conversão falhou: {response.status_code}")

    @task(2)
    def check_job_status(self):
        """
        Task moderada: Verificar status de job (peso 2).

        Verifica status de jobs criados anteriormente.
        """
        if not self.job_ids:
            return  # Sem jobs para verificar

        # Pegar job aleatório da lista
        job_id = random.choice(self.job_ids)

        with self.client.get(
            f"/v1/convert/{job_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if "status" in data:
                    response.success()

                    # Se job completou, remover da lista
                    if data["status"] in ["completed", "failed"]:
                        self.job_ids.remove(job_id)
                else:
                    response.failure("Resposta de status inválida")
            elif response.status_code == 404:
                # Job expirou (normal com TTL)
                self.job_ids.remove(job_id)
                response.success()
            else:
                response.failure(f"Status check falhou: {response.status_code}")


class AdminUser(HttpUser):
    """
    Simula usuário admin que monitora sistema.

    Comportamento:
    - Verifica health checks com mais frequência
    - Monitora métricas
    - Aguarda 0.5-1s entre requisições
    """

    wait_time = between(0.5, 1)
    weight = 1  # 10% dos usuários são admins

    @task(10)
    def monitor_health(self):
        """Monitorar health continuamente."""
        self.client.get("/health")

    @task(5)
    def monitor_metrics(self):
        """Verificar métricas Prometheus."""
        self.client.get("/metrics")


# ========================================
# Event Handlers (Estatísticas)
# ========================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Executado ao iniciar teste."""
    print("\n🚀 Iniciando load test...")
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Executado ao finalizar teste."""
    print("\n✅ Load test concluído!")

    # Estatísticas finais
    stats = environment.stats
    print("\n📊 Estatísticas:")
    print(f"Total de requisições: {stats.total.num_requests}")
    print(f"Requisições falhadas: {stats.total.num_failures}")
    print(f"RPS médio: {stats.total.total_rps:.2f}")
    print(f"Tempo médio de resposta: {stats.total.avg_response_time:.0f}ms")
    print(f"P95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99: {stats.total.get_response_time_percentile(0.99):.0f}ms")

    # Alertas se performance ruim
    if stats.total.avg_response_time > 1000:
        print("\n⚠️  ATENÇÃO: Tempo médio de resposta > 1s")

    if stats.total.num_failures > stats.total.num_requests * 0.01:
        print("\n⚠️  ATENÇÃO: Taxa de erro > 1%")
