from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import redis
import json
import hashlib
import os
import logging

logger = logging.getLogger(__name__)

# Redis Connection for Auth Cache
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r_auth = redis.Redis.from_url(redis_url, decode_responses=True)


# Define HTTPBearer scheme
security = HTTPBearer()

async def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extracts the Bearer token from the Authorization header.
    Validates that the token exists.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Token ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

from app_v5.core.supabase_client import SupabaseService

async def get_current_user(token: str = Depends(get_current_token)):
    """
    Validates the token with Redis cache first, then Supabase.
    TTL: 5 minutes.
    """
    # 1. Gerar Hash do Token (Segurança e Tamanho da Chave)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    cache_key = f"auth_token:{token_hash}"

    try:
        # 2. Tentar Cache Redis (Falha Silenciosa)
        try:
            cached_user = r_auth.get(cache_key)
            if cached_user:
                return json.loads(cached_user)
        except Exception as redis_err:
            logger.warning(f"AUTH CACHE: Redis indisponível, recorrendo ao banco. {redis_err}")

        # 3. Se não houver cache, buscar no Supabase
        supabase = SupabaseService().get_client_for_user(token)
        user_res = await run_in_threadpool(supabase.auth.get_user, token)
        
        if not user_res.user:
             raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
        user_info = {
            "id": user_res.user.id,
            "email": user_res.user.email,
            "access_token": token
        }

        # 4. Salvar no Cache por 5 minutos (Falha Silenciosa)
        try:
            r_auth.setex(cache_key, 300, json.dumps(user_info))
        except Exception as redis_err:
            pass # Apenas ignorar se falhar ao salvar
        
        return user_info

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AUTH ERROR: {str(e)}")
        raise HTTPException(status_code=401, detail="Falha na autenticação.")

