import json
import redis
from config import Config
from utils import setup_logger

logger = setup_logger("queue_consumer")

class QueueConsumer:
    def __init__(self):
        self.client = redis.Redis.from_url(Config.REDIS_URL, decode_responses=True)
        self.queue_name = Config.QUEUE_NAME

    def get_next_job(self) -> dict:
        """Bloqueia até que haja um novo job na fila."""
        logger.info(f"Aguardando jobs na fila: {self.queue_name}...")
        try:
            # BLPOP blocks until an item is available
            result = self.client.blpop(self.queue_name, timeout=0)
            if result:
                _, data = result
                job = json.loads(data)
                logger.info(f"Job recebido: {job.get('chave')}")
                return job
        except redis.ConnectionError as e:
            logger.error(f"Erro de conexão com Redis: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar Job: {e}")
            return None
