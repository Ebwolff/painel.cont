from typing import Dict, Any, List
import logging
from app_v5.services.rule_engine import RuleEngineService

logger = logging.getLogger(__name__)

class TaxValidatorService:
    """
    Motor de validação tributária central.
    Atua como fachada para o RuleEngineService, garantindo auditoria
    complexa (UF/NCM/Regime) em todo o fluxo de upload.
    """

    def __init__(self):
        self.rule_engine = RuleEngineService()

    def validate_taxes(self, nfe_data: Dict[str, Any], empresa_id: str = None) -> Dict[str, Any]:
        """
        Analisa os dados da nota usando o motor de regras especialistas.
        """
        logger.info(f"Iniciando validação inteligente para NFe {nfe_data.get('numero')}")
        
        # O Motor de Regras já lida com NCM, CFOP, CST, UF e Regime internamente
        result = self.rule_engine.validate_nfe(nfe_data, empresa_id=empresa_id)
        
        return result
