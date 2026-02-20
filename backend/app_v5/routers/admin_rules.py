from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app_v5.core.supabase_client import SupabaseService
from app_v5.routers.admin import verify_super_admin
from app_v5.services.external_sync import ExternalSyncService

router = APIRouter(prefix="/admin/rules", tags=["Admin - Fiscal Rules"])
supabase_service = SupabaseService()

class FiscalRuleUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    active: bool = True
    severity: str = 'media'
    expected_rate: float
    ncm: Optional[str] = None
    cfop: Optional[str] = None
    cst: Optional[str] = None
    parameters: dict = {}

@router.get("/", summary="Listar todas as regras fiscais")
async def list_fiscal_rules(client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    res = admin_client.table("fiscal_rules").select("*").order("created_at", desc=True).execute()
    return res.data

@router.post("/", summary="Criar nova regra fiscal manual")
async def create_fiscal_rule(rule: FiscalRuleUpdate, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    res = admin_client.table("fiscal_rules").insert(rule.dict()).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Erro ao criar regra.")
    return res.data[0]

@router.put("/{rule_id}", summary="Atualizar regra fiscal")
async def update_fiscal_rule(rule_id: str, rule: FiscalRuleUpdate, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    res = admin_client.table("fiscal_rules").update(rule.dict()).eq("id", rule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    return res.data[0]

@router.delete("/{rule_id}", summary="Desativar regra fiscal")
async def deactivate_fiscal_rule(rule_id: str, client = Depends(verify_super_admin)):
    admin_client = supabase_service.get_service_client()
    res = admin_client.table("fiscal_rules").update({"active": False}).eq("id", rule_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Regra não encontrada.")
    return {"status": "deactivated"}

@router.post("/sync", summary="Disparar sincronização com fontes externas")
async def trigger_external_sync(client = Depends(verify_super_admin)):
    sync_service = ExternalSyncService()
    try:
        result = await sync_service.sync_federal_rates()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha na sincronização: {str(e)}")
