import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    QUEUE_NAME = os.getenv("QUEUE_NAME", "nfe_download_queue")
    
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:3000/api/webhooks/nfe/status")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
    
    CAPTCHA_SERVICE = os.getenv("CAPTCHA_SERVICE", "2captcha").lower()
    CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY", "")
    
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    DOWNLOADS_DIR = os.getenv("DOWNLOADS_DIR", "./downloads")
    
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", "5"))

    # Sefaz specific Config
    SEFAZ_PORTAL_URL = "https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?tipoConsulta=resumo&tipoConteudo=7PhJ+gAVw2g="
    SEFAZ_SITE_KEY = "0x4AAAAAAADnPIDROmntUZCB" # Standard hCaptcha/reCAPTCHA sitekey (will be detected dynamically)

os.makedirs(Config.DOWNLOADS_DIR, exist_ok=True)
