from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Tuple, Dict
from config import Config
from utils import setup_logger, mask_sensitive_data
import os

logger = setup_logger("browser")

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None

    async def start(self):
        logger.info("Iniciando Playwright...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=Config.HEADLESS,
            args=[
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )

    async def create_context_with_cert(self, pfx_path: str, pfx_password: str) -> Tuple[BrowserContext, Page]:
        """Cria um contexto isolado no navegador injetando o certificado A1."""
        if not os.path.exists(pfx_path):
            raise FileNotFoundError(f"Certificado não encontrado em: {pfx_path}")

        logger.info(f"Criando contexto de navegação com certificado A1 (Senha: {mask_sensitive_data(pfx_password)})")
        
        context = await self.browser.new_context(
            client_certificates=[
                {
                    "origin": "https://www.nfe.fazenda.gov.br",
                    "pfxPath": pfx_path,
                    "passphrase": pfx_password
                }
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        # Interceptamos requisições desnecessárias para acelerar e economizar RAM
        await page.route("**/*.{png,jpg,jpeg,css,woff,woff2}", lambda route: route.abort())
        
        return context, page

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright finalizado.")
