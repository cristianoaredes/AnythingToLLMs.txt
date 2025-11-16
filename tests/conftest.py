"""
Fixtures compartilhadas para testes.
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_redis():
    """Mock do Redis para testes sem dependência real."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.exists.return_value = 1
    mock.hgetall.return_value = {
        "status": "completed",
        "progress": "1.0",
        "result": '{"formats": {"llms": "test content"}}'
    }
    mock.hset.return_value = True
    mock.expire.return_value = True
    return mock


@pytest.fixture
def test_client(mock_redis):
    """Cliente de teste FastAPI com Redis mockado."""
    with patch('src.api.services.conversion_service.redis_client', mock_redis):
        from src.api.main import app
        with TestClient(app) as client:
            yield client


@pytest.fixture
def sample_pdf_content():
    """Conteúdo de PDF de exemplo para testes."""
    # PDF mínimo válido
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000056 00000 n\n0000000114 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n224\n%%EOF"


@pytest.fixture
def api_headers():
    """Headers padrão para requisições à API."""
    return {
        "X-API-Key": os.getenv("LLMS_API_KEY", "test-key-123")
    }


@pytest.fixture
def mock_document_converter():
    """Mock do DocumentConverterTool."""
    mock = MagicMock()
    mock.run.return_value = {
        "formats": {
            "llms": "# Test Document\n\nTest content",
            "md": "# Test Document\n\nTest content"
        },
        "doc": MagicMock()
    }
    return mock
