from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import json
import hashlib
import os
import logging
import time

logger = logging.getLogger(__name__)

# Define HTTPBearer scheme
security = HTTPBearer()

# In-memory auth cache (TTL 5 minutes)
_auth_cache: dict = {}
_AUTH_CACHE_TTL = 300

async def get_current_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado. Token ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

from app_v5.core.supabase_client import SupabaseService

async def get_current_user(token: str = Depends(get_current_token)):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    cache_key = f"auth_token:{token_hash}"

    # 1. Check in-memory cache first
    cached = _auth_cache.get(cache_key)
    if cached and (time.time() - cached['ts']) < _AUTH_CACHE_TTL:
        return cached['data']

    try:
        # 2. Cache miss — validate with Supabase
        logger.info(f"AUTH CACHE MISS: Validating token with Supabase: {token[:10]}...")
        supabase = SupabaseService().get_client_for_user(token)
        user_res = await run_in_threadpool(supabase.auth.get_user, token)
        
        if not user_res.user:
             logger.error("AUTH ERROR: supabase.auth.get_user returned no user.")
             raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
        user_info = {
            "id": user_res.user.id,
            "email": user_res.user.email,
            "access_token": token
        }

        # 3. Store in cache
        _auth_cache[cache_key] = {'data': user_info, 'ts': time.time()}

        # 4. Evict old entries (keep cache bounded)
        if len(_auth_cache) > 500:
            oldest_key = min(_auth_cache, key=lambda k: _auth_cache[k]['ts'])
            del _auth_cache[oldest_key]

        return user_info

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"AUTH EXCEPTION: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Falha na autenticação.")


