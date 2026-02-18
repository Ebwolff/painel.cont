from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from fastapi.concurrency import run_in_threadpool

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

from app_v5.v5.core.supabase_client import SupabaseService

async def get_current_user(token: str = Depends(get_current_token)):
    """
    Validates the token with Supabase (async threadpool) and returns the user object.
    This acts as a dependency for protected routes.
    """
    supabase = SupabaseService().get_client_for_user(token)
    try:
        # Executar chamada bloqueante em thread separada
        user_res = await run_in_threadpool(supabase.auth.get_user, token)
        
        if not user_res.user:
             raise HTTPException(status_code=401, detail="Token inválido ou expirado")
        
        return {
            "id": user_res.user.id,
            "email": user_res.user.email,
            "access_token": token
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Erro de autenticação: {str(e)}")
