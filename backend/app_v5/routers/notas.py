from fastapi import APIRouter, Depends, HTTPException, Query
from app_v5.core.supabase_client import SupabaseService
from app_v5.core.security import get_current_user
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
supabase_service = SupabaseService()

@router.get("/", summary="Lista notas fiscais com filtros")
async def list_invoices(
    empresa_id: Optional[str] = None,
    direcao: Optional[str] = Query(None, enum=["entrada", "saida"], description="entrada = Recebidas, saida = Emitidas"),
    status: Optional[str] = None,
    search: Optional[str] = None,
    dt_inicio: Optional[str] = Query(None, description="Data Inicial (YYYY-MM-DD)"),
    dt_fim: Optional[str] = Query(None, description="Data Final (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user)
):
    """
    Lista as notas fiscais do tenant, permitindo filtrar por empresa e direção.
    """
    try:
        user_id = user['id']
        admin_client = supabase_service.get_service_client()
        
        # 1. Obter perfil e tenant
        profile_res = admin_client.table("profiles").select("tenant_id, role, empresa_id").eq("id", user_id).single().execute()
        profile = profile_res.data
        tenant_id = profile.get("tenant_id")
        user_role = profile.get("role")
        
        if not tenant_id:
            raise HTTPException(status_code=403, detail="Escritório não identificado.")

        # 2. Obter CNPJs das empresas do tenant (ou da empresa específica se role=monitor)
        query_cnpjs = admin_client.table("empresas").select("cnpj").eq("tenant_id", tenant_id)
        
        target_empresa_id = empresa_id
        if user_role == 'monitor':
            target_empresa_id = profile.get("empresa_id")
            
        if target_empresa_id:
            query_cnpjs = query_cnpjs.eq("id", target_empresa_id)
            
        cnpjs_res = query_cnpjs.execute()
        cnpjs = [e["cnpj"] for e in (cnpjs_res.data or []) if e.get("cnpj")]

        # 3. Construir Query de Notas
        query = admin_client.table("notas_fiscais").select("*, empresas(razao_social)", count="exact").eq("tenant_id", tenant_id)

        if target_empresa_id:
            query = query.eq("empresa_id", target_empresa_id)
        
        if status:
            query = query.eq("status", status)
            
        if search:
            query = query.or_(f"numero.ilike.%{search}%,chave_acesso.ilike.%{search}%")
            
        if dt_inicio:
            query = query.gte("data_emissao", f"{dt_inicio}T00:00:00Z")
            
        if dt_fim:
            query = query.lte("data_emissao", f"{dt_fim}T23:59:59Z")

        # Filtro de Direção (Robustamente baseado no emitente)
        if direcao == "saida":
            # Emitidas: emitente_cnpj está na lista de CNPJs do escritório
            if cnpjs:
                query = query.in_("emitente_cnpj", cnpjs)
            else:
                return {"data": [], "total": 0, "page": page, "limit": limit}
        elif direcao == "entrada":
            # Recebidas: emitente_cnpj NÃO está na lista (fallback seguro para resumos)
            if cnpjs:
                query = query.not_.in_("emitente_cnpj", cnpjs)
            else:
                return {"data": [], "total": 0, "page": page, "limit": limit}

        # Paginação
        start = (page - 1) * limit
        end = start + limit - 1
        
        res = query.order("data_emissao", desc=True).range(start, end).execute()
        
        return {
            "data": res.data or [],
            "total": res.count or 0,
            "page": page,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"NOTAS: Erro ao listar notas: {e}")
        raise HTTPException(status_code=500, detail=str(e))
