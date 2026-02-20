import logging
from typing import List, Dict, Any
from app_v5.core.supabase_client import SupabaseService
from datetime import datetime

logger = logging.getLogger(__name__)

class ExternalSyncService:
    """
    Serviço para sincronização de regras fiscais com fontes externas (IBPT/IOB Simulado).
    Responsável por manter a tabela 'fiscal_rules' atualizada.
    """
    
    def __init__(self):
        self.supabase = SupabaseService()
        self.admin_client = self.supabase.get_service_client()

    async def sync_federal_rates(self) -> Dict[str, Any]:
        """
        Sincroniza alíquotas oficiais vigentes e projeções da Reforma Tributária.
        """
        logger.info("Iniciando sincronização de regras fiscais externas...")
        
        # Simulação        # Dados de APIs Oficiais (IBPT/IOB/CENOFISCO)
        # Obs: Alíquotas estaduais de ICMS NÃO estão aqui — foram populadas via migration 007_icms_nacional.sql
        external_data = [
            # --- TRIBUTOS VIGENTES (Legislação Nacional) ---
            {"rule_type": "pis", "rate": 0.0165, "name": "PIS - Alíquota Geral (Não-Cumulativo)", "severity": "media"},
            {"rule_type": "cofins", "rate": 0.076, "name": "COFINS - Alíquota Geral (Não-Cumulativo)", "severity": "media"},

            # --- REFORMA TRIBUTÁRIA (Projeções Comitê Gestor) ---
            {"rule_type": "cbs", "rate": 0.009, "name": "CBS - Alíquota de Teste (Reforma 2026)", "severity": "alta"},
            {"rule_type": "ibs", "rate": 0.001, "name": "IBS - Alíquota de Teste (Reforma 2026)", "severity": "alta"},

            # Tratamento Diferenciado — Alimentos (NCM 02)
            {"ncm": "02", "rule_type": "cbs", "rate": 0.0, "name": "CBS - Alimentos (Cesta Básica)", "severity": "critica"},
            {"ncm": "02", "rule_type": "ibs", "rate": 0.0, "name": "IBS - Alimentos (Cesta Básica)", "severity": "critica"},
        ]
        
        updated_count = 0
        created_count = 0
        
        for rule_data in external_data:
            # Tentar encontrar regra existente
            query = self.admin_client.table("fiscal_rules").select("id")
            
            if rule_data.get("ncm"):
                query = query.eq("ncm", rule_data["ncm"])
            if rule_data.get("cfop"):
                query = query.eq("cfop", rule_data["cfop"])
                
            query = query.eq("rule_type", rule_data["rule_type"])
            
            res = query.execute()
            
            payload = {
                "name": rule_data["name"],
                "rule_type": rule_data["rule_type"],
                "expected_rate": rule_data["rate"],
                "ncm": rule_data.get("ncm"),
                "cfop": rule_data.get("cfop"),
                "severity": rule_data.get("severity", "baixa"),
                "active": True,
                "version": f"sync-{datetime.now().strftime('%Y%m%d')}",
                "last_checked_at": datetime.now().isoformat(),
                "legal_foundation": rule_data.get("legal_foundation", "Legislação Tributária Vigente"),
                "parameters": {"source": "oficial_api_integradora", "sync_at": datetime.now().isoformat()}
            }
            
            if res.data and len(res.data) > 0:
                # Update
                rule_id = res.data[0]["id"]
                self.admin_client.table("fiscal_rules").update(payload).eq("id", rule_id).execute()
                updated_count += 1
            else:
                # Insert
                self.admin_client.table("fiscal_rules").insert(payload).execute()
                created_count += 1
                
        logger.info(f"Sincronização concluída: {created_count} novas, {updated_count} atualizadas.")
        
        return {
            "status": "success",
            "created": created_count,
            "updated": updated_count,
            "timestamp": datetime.now().isoformat()
        }
