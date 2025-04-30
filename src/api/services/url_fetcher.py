"""
Serviço para buscar páginas dinâmicas via Playwright.
"""
from playwright.async_api import async_playwright
import tempfile

async def fetch_and_save_url(url: str) -> str:
    """
    Navega até a URL usando um browser headless, espera o carregamento de rede e salva o HTML em arquivo temporário.

    Args:
        url: URL da página a ser buscada
    Returns:
        path para o arquivo HTML salvo
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        html = await page.content()
        await browser.close()

    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    tmp_file.write(html.encode('utf-8'))
    tmp_file.close()
    return tmp_file.name 