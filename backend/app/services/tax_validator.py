from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TaxValidatorService:
    """
    Motor de validação tributária focado na Reforma 2026.
    Verifica conformidade de CBS (0.9%) e IBS (0.1%).
    """

    # Configuração default (Pode vir de um DB ou Settings)
    DEFAULT_CONFIG = {
        "cbs_rate": 0.009,
        "ibs_rate": 0.001,
        "tolerance": 0.05
    }

    def validate_taxes(self, nfe_data: Dict[str, Any], config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analisa os dados da nota conforme parâmetros de transição configuráveis.
        """
        conf = config or self.DEFAULT_CONFIG
        cbs_rate = conf.get("cbs_rate", 0.009)
        ibs_rate = conf.get("ibs_rate", 0.001)
        tolerance = conf.get("tolerance", 0.05)

        valor_total = nfe_data.get("valor_total", 0.0)
        cbs_destacado = nfe_data.get("valor_cbs", 0.0)
        ibs_destacado = nfe_data.get("valor_ibs", 0.0)

        cbs_esperado = round(valor_total * cbs_rate, 2)
        ibs_esperado = round(valor_total * ibs_rate, 2)

        alertas = []

        # Validação CBS
        cbs_diff = abs(cbs_destacado - cbs_esperado)
        cbs_ok = cbs_diff <= tolerance
        
        if not cbs_ok:
            alertas.append({
                "tipo": "cbs_incorreto",
                "severidade": "alta",
                "mensagem": f"Valor de CBS incorreto. Esperado: R$ {cbs_esperado}, Encontrado: R$ {cbs_destacado}",
                "valor_esperado": cbs_esperado,
                "valor_encontrado": cbs_destacado,
                "diferenca": cbs_diff
            })

        # Validação IBS
        ibs_diff = abs(ibs_destacado - ibs_esperado)
        ibs_ok = ibs_diff <= tolerance

        if not ibs_ok:
            alertas.append({
                "tipo": "ibs_incorreto",
                "severidade": "alta",
                "mensagem": f"Valor de IBS incorreto. Esperado: R$ {ibs_esperado}, Encontrado: R$ {ibs_destacado}",
                "valor_esperado": ibs_esperado,
                "valor_encontrado": ibs_destacado,
                "diferenca": ibs_diff
            })

        # Definição de Status
        if not cbs_ok or not ibs_ok:
            status = "irregular"
        elif valor_total == 0:
            status = "erro_parse" # Ou nota zerada
        else:
            status = "conforme"

        return {
            "status": status,
            "validation_details": {
                "cbs_esperado": cbs_esperado,
                "ibs_esperado": ibs_esperado,
                "cbs_ok": cbs_ok,
                "ibs_ok": ibs_ok
            },
            "alertas": alertas
        }
