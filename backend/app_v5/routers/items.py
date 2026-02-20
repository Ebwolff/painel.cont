from fastapi import APIRouter, Depends, HTTPException
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user
from typing import List

router = APIRouter()
supabase_service = SupabaseService()

@router.get("/{nota_id}", summary="Busca detalhes e itens de uma nota")
def get_nfe_items(nota_id: str, user: dict = Depends(get_current_user)):
    """
    Retorna os itens detalhados de uma nota fiscal, incluindo auditoria por item.
    """
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Obter tenant_id
        profile_res = admin_client.table("profiles").select("tenant_id").eq("id", user_id).single().execute()
        tenant_id = profile_res.data.get("tenant_id") if profile_res.data else None
        
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Escritório não identificado.")

        # 2. Buscar itens (Garante que só busca do próprio tenant)
        res = admin_client.table("nfe_items")\
            .select("*")\
            .eq("nota_fiscal_id", nota_id)\
            .eq("tenant_id", tenant_id)\
            .order("n_item", desc=False)\
            .execute()
            
        return res.data or []
    except Exception as e:
        print(f"Erro ao buscar itens da nota {nota_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar detalhes da nota.")
