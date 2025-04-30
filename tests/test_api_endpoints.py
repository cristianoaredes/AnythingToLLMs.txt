import pytest
import asyncio
import json
from httpx import AsyncClient, ASGITransport
from src.api.main import app

@pytest.mark.asyncio
async def test_analyzer_tokens_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Use app directly with transport param
        response = await ac.post("/v1/analyzer/tokens", json={"content": "# Title\nHello World", "model_name": "gpt-3.5-turbo"})
        assert response.status_code == 200
        json_data = response.json()
        assert "total_tokens" in json_data and isinstance(json_data["total_tokens"], int)
        assert json_data["total_tokens"] >= 0
        assert "sections" in json_data

@pytest.mark.asyncio
async def test_detect_content_type_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        data = {"content": "# Section\nTest Content", "model_name": "gpt-3.5-turbo"}
        response = await ac.post("/v1/analyzer/detect-content-type", json=data)
        assert response.status_code == 200
        resp = response.json()
        assert "content_type" in resp
        assert "chunking_recommendation" in resp

@pytest.mark.asyncio
async def test_convert_invalid_file_extension():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test.exe", b"fake content")}  # extensão não suportada
        response = await ac.post("/v1/convert/", files=files)
        assert response.status_code == 400

@pytest.mark.skip(reason="Requires Redis connection")
@pytest.mark.asyncio
async def test_convert_and_status_txt_file(tmp_path):
    # Cria arquivo de texto simples
    file_path = tmp_path / "sample.txt"
    file_path.write_text("Hello World")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("sample.txt", file_path.read_bytes())}
        params = {"profile": "llms-min", "output_formats": ["llms"], "model_name": "gpt-3.5-turbo"}
        # Envia o job de conversão
        response = await ac.post(
            "/v1/convert/",
            files=files,
            data={"params": json.dumps(params)}
        )
        assert response.status_code == 200
        body = response.json()
        assert "job_id" in body
        job_id = body["job_id"]

        # Consulta o status até completar
        status_data = None
        for _ in range(10):
            status_r = await ac.get(f"/v1/convert/{job_id}")
            assert status_r.status_code == 200
            status_data = status_r.json()
            if status_data["status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(0.5)

        assert status_data is not None
        assert status_data["status"] == "completed"
        assert status_data.get("result") is not None
        formats = status_data["result"]["formats"]
        assert "llms" in formats
        # Deve conter título no formato llms.txt
        assert formats["llms"].startswith("# Title")