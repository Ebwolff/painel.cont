import logging
from typing import Dict, Any, List, Optional
from app_v5.services.rule_engine import RuleEngineService

logger = logging.getLogger(__name__)

class SimulationService:
    """
    Serviço central para cálculos tributários e simulações.
    Reutiliza o RuleEngine para garantir consistência entre o monitor real e os simuladores.
    """

    def __init__(self):
        self.rule_engine = RuleEngineService()

    def simulate_nfe_compliance(self, nfe_mock_data: Dict[str, Any], regime: str = "lucro_real") -> Dict[str, Any]:
        """
        Simula a conformidade de uma nota rascunhada.
        Recebe dados simplificados e retorna o veredito tributário.
        """
        logger.info(f"Simulando conformidade para nota rascunho...")
        
        # O validate_nfe já lida com a lógica de busca de regras
        # Precisamos garantir que os dados de entrada estejam no formato esperado pelo motor
        # nfe_data esperado: { "emitente_uf", "destinatario_uf", "itens": [...] }
        
        result = self.rule_engine.validate_nfe(nfe_mock_data)
        
        # Calcular Score de Conformidade (0 a 100)
        total_items = len(nfe_mock_data.get("itens", []))
        if total_items == 0:
            return {**result, "compliance_score": 100}
            
        items_with_issues = result.get("validation_details", {}).get("items_with_issues", 0)
        score = max(0, 100 - (items_with_issues / total_items * 100))
        
        return {
            **result,
            "compliance_score": round(score, 1),
            "recomendacao": "Nota em conformidade" if score == 100 else "Revisão necessária nos itens apontados"
        }

    def calculate_assisted_preview(self, notas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolida a apuração assistida (IBS/CBS) baseada em uma lista de notas.
        """
        total_cbs = 0.0
        total_ibs = 0.0
        total_base = 0.0
        
        for nota in notas:
            total_base += float(nota.get("valor_total", 0) or 0)
            total_cbs += float(nota.get("valor_cbs", 0) or 0)
            total_ibs += float(nota.get("valor_ibs", 0) or 0)
            
        return {
            "periodo": "Mensal",
            "faturamento_bruto": round(total_base, 2),
            "consolidado": {
                "cbs": round(total_cbs, 2),
                "ibs": round(total_ibs, 2),
                "total_tributos": round(total_cbs + total_ibs, 2)
            },
            "aliquota_efetiva": round(((total_cbs + total_ibs) / total_base * 100), 2) if total_base > 0 else 0
        }
