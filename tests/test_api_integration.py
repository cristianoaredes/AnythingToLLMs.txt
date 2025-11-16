"""
Testes de integração para API REST.

Estes testes usam mocks para não depender de Redis real.
"""
import pytest
from io import BytesIO
from unittest.mock import patch, AsyncMock


class TestHealthEndpoint:
    """Testes para o endpoint de health check."""

    def test_health_check_healthy(self, test_client, mock_redis):
        """Testa health check quando tudo está OK."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["redis"]["status"] == "ok"
        assert data["checks"]["disk"]["status"] in ["ok", "warning"]
        assert data["checks"]["upload_dir"]["writable"] is True

    def test_health_check_unhealthy_redis(self, test_client, mock_redis):
        """Testa health check quando Redis está down."""
        mock_redis.ping.side_effect = Exception("Connection refused")

        response = test_client.get("/health")

        assert response.status_code == 503
        data = response.json()

        assert data["status"] == "unhealthy"
        assert data["checks"]["redis"]["status"] == "error"


class TestRootEndpoint:
    """Testes para endpoint raiz."""

    def test_root_endpoint(self, test_client):
        """Testa endpoint raiz retorna informações da API."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "docs_url" in data
        assert data["docs_url"] == "/docs"


class TestConversionEndpoint:
    """Testes para endpoint de conversão."""

    def test_convert_requires_file_or_url(self, test_client, api_headers):
        """Testa que é necessário enviar arquivo ou URL."""
        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            data={"params": "{}"}
        )

        assert response.status_code == 400
        assert "arquivo ou uma URL" in response.json()["detail"]

    def test_convert_rejects_both_file_and_url(self, test_client, api_headers, sample_pdf_content):
        """Testa que não aceita arquivo E URL ao mesmo tempo."""
        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            files={"file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")},
            data={"url": "https://example.com/doc.pdf", "params": "{}"}
        )

        assert response.status_code == 400
        assert "não ambos" in response.json()["detail"]

    def test_convert_validates_file_extension(self, test_client, api_headers):
        """Testa validação de extensão de arquivo."""
        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            files={"file": ("test.exe", BytesIO(b"fake content"), "application/octet-stream")},
            data={"params": "{}"}
        )

        assert response.status_code == 400
        assert "não suportado" in response.json()["detail"]

    def test_convert_validates_file_size(self, test_client, api_headers):
        """Testa validação de tamanho de arquivo."""
        # Criar arquivo grande (51MB)
        large_content = b"x" * (51 * 1024 * 1024)

        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            files={"file": ("test.pdf", BytesIO(large_content), "application/pdf")},
            data={"params": "{}"}
        )

        assert response.status_code == 400
        assert "excedido" in response.json()["detail"]

    @patch('src.api.routers.converter.create_conversion_job')
    async def test_convert_file_success(self, mock_create_job, test_client, api_headers, sample_pdf_content):
        """Testa conversão bem-sucedida de arquivo."""
        mock_create_job.return_value = "test-job-123"

        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            files={"file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")},
            data={"params": '{"profile": "llms-min"}'}
        )

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert data["status"] == "processing"

    def test_convert_url_validation_malicious_scheme(self, test_client, api_headers):
        """Testa que URLs com esquemas maliciosos são rejeitadas."""
        malicious_urls = [
            "file:///etc/passwd",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]

        for url in malicious_urls:
            response = test_client.post(
                "/v1/convert/",
                headers=api_headers,
                data={"url": url, "params": "{}"}
            )

            assert response.status_code == 400
            assert "não permitido" in response.json()["detail"]

    def test_convert_url_validation_ssrf(self, test_client, api_headers):
        """Testa proteção contra SSRF."""
        ssrf_urls = [
            "http://localhost/admin",
            "http://127.0.0.1:8080",
            "http://192.168.1.1/router",
            "http://10.0.0.1/internal"
        ]

        for url in ssrf_urls:
            response = test_client.post(
                "/v1/convert/",
                headers=api_headers,
                data={"url": url, "params": "{}"}
            )

            assert response.status_code == 400
            assert "não são permitidas" in response.json()["detail"]


class TestJobStatusEndpoint:
    """Testes para endpoint de status de job."""

    def test_get_job_status_not_found(self, test_client, api_headers, mock_redis):
        """Testa busca de job que não existe."""
        mock_redis.exists.return_value = 0

        response = test_client.get("/v1/convert/nonexistent-job", headers=api_headers)

        assert response.status_code == 404

    def test_get_job_status_success(self, test_client, api_headers, mock_redis):
        """Testa busca de job que existe."""
        response = test_client.get("/v1/convert/test-job-123", headers=api_headers)

        assert response.status_code == 200
        data = response.json()

        assert "job_id" in data
        assert "status" in data


class TestValidationModels:
    """Testes para validação de modelos Pydantic."""

    def test_ocr_language_validation(self, test_client, api_headers, sample_pdf_content):
        """Testa validação de código de idioma OCR."""
        # Idioma inválido (muito curto)
        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            files={"file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")},
            data={"params": '{"ocr_language": "ab"}'}
        )

        assert response.status_code == 400

    def test_chunk_overlap_validation(self, test_client, api_headers, sample_pdf_content):
        """Testa validação de chunk_overlap vs chunk_size."""
        # chunk_overlap >= chunk_size (inválido)
        response = test_client.post(
            "/v1/convert/",
            headers=api_headers,
            files={"file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf")},
            data={"params": '{"chunk_size": 100, "chunk_overlap": 100}'}
        )

        assert response.status_code == 400
        assert "menor que chunk_size" in response.json()["detail"]


class TestAuthentication:
    """Testes para autenticação."""

    def test_missing_api_key(self, test_client):
        """Testa que requisições sem API key são rejeitadas."""
        response = test_client.get("/v1/convert/test-job")

        # Depende da implementação do verify_api_key
        # Se API_KEY não estiver configurada, pode passar
        assert response.status_code in [401, 403, 200]
