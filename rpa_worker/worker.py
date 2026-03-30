import asyncio
import aiohttp
import traceback
from config import Config
from queue import QueueConsumer
from browser import BrowserManager
from captcha_solver import CaptchaSolver
from sefaz_bot import SefazBot, SefazBotError
from utils import setup_logger

logger = setup_logger("worker")

class RPAWorker:
    def __init__(self):
        self.queue = QueueConsumer()
        self.browser_manager = BrowserManager()
        self.captcha_solver = CaptchaSolver()

    async def send_webhook(self, payload: dict):
        """Notifica o SaaS Backend via Webhook."""
        headers = {"Authorization": f"Bearer {Config.WEBHOOK_SECRET}"}
        logger.info(f"Enviando Webhook para {Config.WEBHOOK_URL} com status: {payload.get('status')}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(Config.WEBHOOK_URL, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
        except Exception as e:
            logger.error(f"Falha ao enviar webhook: {str(e)}")

    async def process_job(self, job: dict):
        chave = job.get("chave")
        empresa_id = job.get("empresa_id")
        pfx_path = job.get("pfx_path") # Caminho local montado no volume do container
        pfx_password = job.get("pfx_password")
        
        if not all([chave, empresa_id, pfx_path, pfx_password]):
            logger.error(f"Job malformado: {job}")
            return

        logger.info(f"Iniciando processamento NFe: {chave} - Empresa: {empresa_id}")
        
        context, page = None, None
        success = False
        xml_filepath = None
        error_message = None

        for attempt in range(1, Config.MAX_RETRIES + 1):
            try:
                # 1. Cria contexto de navegação com o .PFX dessa empresa
                logger.info(f"Tentativa {attempt}/{Config.MAX_RETRIES}...")
                context, page = await self.browser_manager.create_context_with_cert(pfx_path, pfx_password)
                
                # 2. Instancia o Bot e executa o fluxo
                bot = SefazBot(page, self.captcha_solver)
                xml_filepath = await bot.download_xml(chave)
                
                success = True
                break # Sai do retry loop

            except SefazBotError as e:
                error_message = str(e)
                logger.warning(f"Erro SEFAZ na tentativa {attempt}: {error_message}")
            except Exception as e:
                error_message = traceback.format_exc()
                logger.error(f"Erro Crítico na tentativa {attempt}:\n{error_message}")
            finally:
                if context:
                    await context.close()
            
            if not success and attempt < Config.MAX_RETRIES:
                await asyncio.sleep(Config.RETRY_DELAY_SECONDS * attempt) # Backoff Progressivo

        # 3. Notificar Backend (Upload Simulado/Direto para a API)
        # Em um cenário real, você abriria o arquivo XML em memória e faria upload pro S3 ou para o backend diretamente no Webhook.
        payload = {
            "empresa_id": empresa_id,
            "chave": chave,
            "status": "COMPLETO" if success else "ERRO",
            "source": "RPA",
        }
        
        if success:
            payload["xml_url"] = f"file://{xml_filepath}"
            # payload["xml_base64"] = encode_base64(...)
        else:
            payload["error_details"] = error_message

        await self.send_webhook(payload)
        logger.info(f"Job finalizado: {chave}")

    async def run(self):
        logger.info("RPA Worker Iniciado. Conectando dependências...")
        await self.browser_manager.start()
        
        try:
            while True:
                # Polling síncrono no Redis, mas em thread separada com asyncio.to_thread para não travar o loop
                job = await asyncio.to_thread(self.queue.get_next_job)
                if job:
                    await self.process_job(job)
        except asyncio.CancelledError:
            logger.info("Worker cancelado.")
        finally:
            await self.browser_manager.stop()
