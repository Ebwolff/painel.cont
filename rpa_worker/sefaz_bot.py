import os
import asyncio
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from config import Config
from captcha_solver import CaptchaSolver
from utils import setup_logger

logger = setup_logger("sefaz_bot")

class SefazBotError(Exception):
    pass

class SefazBot:
    def __init__(self, page: Page, captcha_solver: CaptchaSolver):
        self.page = page
        self.solver = captcha_solver

    async def download_xml(self, chave: str) -> str:
        """Consulta a chave na SEFAZ, resolve o captcha e baixa o XML."""
        logger.info(f"[{chave}] Acessando portal da SEFAZ...")
        
        try:
            await self.page.goto(Config.SEFAZ_PORTAL_URL, wait_until="networkidle", timeout=30000)
            
            # Adicionar a chave
            await self.page.fill("#ctl00_ContentPlaceHolder1_txtChaveAcessoCompleta", chave)
            logger.info(f"[{chave}] Chave preenchida. Resolvendo CAPTCHA...")

            # O site da SEFAZ muitas vezes expõe a sitekey direto no HTML
            # Para hCaptcha, vamos tentar localizar a sitekey
            sitekey_element = await self.page.query_selector('.h-captcha')
            sitekey = await sitekey_element.get_attribute('data-sitekey') if sitekey_element else Config.SEFAZ_SITE_KEY

            token = await self.solver.solve(sitekey, self.page.url)

            # Injetar o token no formulário
            logger.info(f"[{chave}] Injetando token hCaptcha no navegador...")
            await self.page.evaluate(f'''() => {{
                document.querySelector('[name=h-captcha-response]').innerHTML = "{token}";
                document.querySelector('[name=g-recaptcha-response]').innerHTML = "{token}";
            }}''')

            # Clicar em Consultar
            await self.page.click("#ctl00_ContentPlaceHolder1_btnConsultar")
            logger.info(f"[{chave}] Consulta submetida. Aguardando processamento...")

            # Aguardar o carregamento da próxima página
            await self.page.wait_for_load_state("networkidle")

            # Checar se deu erro de nota não encontrada ou inválida
            error_msg = await self.page.query_selector("#ctl00_ContentPlaceHolder1_lblMsgErro")
            if error_msg:
                text = await error_msg.inner_text()
                if text.strip():
                    raise SefazBotError(f"SEFAZ retornou erro: {text.strip()}")

            # Procurar botão de Download
            download_btn = await self.page.query_selector("input[value='Download do documento'], input[id*='btnDownload']")
            if not download_btn:
                raise SefazBotError("Botão de Download do documento não encontrado! (Possivelmente certificado inválido, sem permissão ou layout alterado).")

            logger.info(f"[{chave}] Iniciando download do XML...")
            
            async with self.page.expect_download(timeout=15000) as download_info:
                # Pode haver um popup JS "Confirma o download?"
                self.page.once("dialog", lambda dialog: dialog.accept())
                await download_btn.click()
            
            download = await download_info.value
            filepath = os.path.join(Config.DOWNLOADS_DIR, f"{chave}.xml")
            await download.save_as(filepath)
            
            logger.info(f"[{chave}] XML baixado com sucesso: {filepath}")
            return filepath

        except PlaywrightTimeoutError:
            raise SefazBotError("Timeout de conexão na SEFAZ ou ao aguardar elementos.")
        except Exception as e:
            raise SefazBotError(f"Falha inesperada: {str(e)}")
