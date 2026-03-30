import asyncio
import aiohttp
from config import Config
from utils import setup_logger

logger = setup_logger("captcha_solver")

class CaptchaSolverError(Exception):
    pass

class CaptchaSolver:
    def __init__(self):
        self.api_key = Config.CAPTCHA_API_KEY
        self.service = Config.CAPTCHA_SERVICE

    async def solve(self, sitekey: str, pageurl: str) -> str:
        if not self.api_key:
            raise CaptchaSolverError("CAPTCHA_API_KEY is not configured.")
        
        if self.service == "2captcha":
            return await self._solve_2captcha(sitekey, pageurl)
        elif self.service == "anticaptcha":
            return await self._solve_anticaptcha(sitekey, pageurl)
        else:
            raise CaptchaSolverError(f"Unsupported captcha service: {self.service}")

    async def _solve_2captcha(self, sitekey: str, pageurl: str) -> str:
        logger.info("Enviando desafio hCaptcha para 2Captcha...")
        async with aiohttp.ClientSession() as session:
            # 1. Enviar requisição
            in_url = f"http://2captcha.com/in.php?key={self.api_key}&method=hcaptcha&sitekey={sitekey}&pageurl={pageurl}&json=1"
            async with session.get(in_url) as resp:
                result = await resp.json()
                if result.get("status") != 1:
                    raise CaptchaSolverError(f"Erro ao enviar captcha: {result.get('request')}")
                
                request_id = result.get("request")
                logger.info(f"Captcha enviado. Request ID: {request_id}. Aguardando solução...")

            # 2. Aguardar resultado (Polling)
            res_url = f"http://2captcha.com/res.php?key={self.api_key}&action=get&id={request_id}&json=1"
            await asyncio.sleep(15) # Wait before first check
            
            for _ in range(30): # Timeout ~ 150 seconds
                async with session.get(res_url) as resp:
                    result = await resp.json()
                    status = result.get("status")
                    text = result.get("request")
                    
                    if status == 1:
                        logger.info("Captcha resolvido com sucesso!")
                        return text
                    elif text == "CAPCHA_NOT_READY":
                        await asyncio.sleep(5)
                    else:
                        raise CaptchaSolverError(f"Erro na resolução: {text}")

            raise CaptchaSolverError("Timeout aguardando solução do Captcha.")

    async def _solve_anticaptcha(self, sitekey: str, pageurl: str) -> str:
        logger.info("Enviando desafio hCaptcha para AntiCaptcha...")
        async with aiohttp.ClientSession() as session:
            url_task = "https://api.anti-captcha.com/createTask"
            payload = {
                "clientKey": self.api_key,
                "task": {
                    "type": "HCaptchaTaskProxyless",
                    "websiteURL": pageurl,
                    "websiteKey": sitekey
                }
            }
            async with session.post(url_task, json=payload) as resp:
                res = await resp.json()
                if res.get("errorId") != 0:
                    raise CaptchaSolverError(f"Erro ao criar task: {res.get('errorDescription')}")
                task_id = res.get("taskId")
                logger.info(f"Task criada. ID: {task_id}. Aguardando solução...")

            url_result = "https://api.anti-captcha.com/getTaskResult"
            payload_result = {
                "clientKey": self.api_key,
                "taskId": task_id
            }
            
            await asyncio.sleep(15)
            for _ in range(30):
                async with session.post(url_result, json=payload_result) as resp:
                    res = await resp.json()
                    status = res.get("status")
                    
                    if status == "ready":
                        logger.info("Captcha resolvido com sucesso!")
                        return res.get("solution").get("gRecaptchaResponse")
                    elif status == "processing":
                        await asyncio.sleep(5)
                    else:
                        raise CaptchaSolverError(f"Erro na resolução: {res.get('errorDescription')}")

            raise CaptchaSolverError("Timeout aguardando solução do Captcha.")
