import asyncio
from worker import RPAWorker
from utils import setup_logger

logger = setup_logger("main")

async def main():
    logger.info("Inicializando Motor RPA de Captura SEFAZ...")
    worker = RPAWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Desligamento manual detectado (Ctrl+C).")
    except Exception as e:
        logger.error(f"Worker falhou criticamente: {e}")

if __name__ == "__main__":
    asyncio.run(main())
