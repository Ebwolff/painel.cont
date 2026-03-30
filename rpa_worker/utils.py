import logging
import sys

def setup_logger(name: str):
    """Configura um logger estruturado para o RPA."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def mask_sensitive_data(data: str, visible_chars=4) -> str:
    """Mascarar dados sensíveis como senhas e chaves."""
    if not data or len(data) <= visible_chars:
        return '***'
    return f"{'*' * (len(data) - visible_chars)}{data[-visible_chars:]}"
