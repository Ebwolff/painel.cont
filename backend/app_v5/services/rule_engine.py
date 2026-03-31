from typing import Dict, Any, List, Optional
import logging
import json
import os


from app_v5.core.supabase_client import SupabaseService

logger = logging.getLogger(__name__)


class RuleEngineService:
    """
    Motor de Regras Fiscais Modular.
    Busca regras no banco de dados e cruza com os dados extraídos de cada item da NF-e.
    """

    def __init__(self):
        self.supabase = SupabaseService()
        self._rules_cache: List[Dict] = []
        self._cache_loaded = False


    def _load_rules(self):
        """Carrega regras do cache em memória ou do Banco."""
        if self._cache_loaded and self._rules_cache:
            return

        try:
            # Carregar do Supabase
            client = self.supabase.get_service_client()
            res = client.table("fiscal_rules").select("*").eq("active", True).execute()
            self._rules_cache = res.data or []
            
            self._cache_loaded = True
            logger.info(f"RuleEngine: {len(self._rules_cache)} regras carregadas via DB.")
        except Exception as e:
            logger.error(f"RuleEngine: Falha ao carregar regras: {e}")
            self._rules_cache = []

    def invalidate_cache(self):
        """Força recarga das regras."""
        self._cache_loaded = False
        self._rules_cache = []


    def _find_matching_rules(
        self,
        ncm: Optional[str],
        cfop: Optional[str],
        cst: Optional[str],
        origin_uf: Optional[str] = None,
        dest_uf: Optional[str] = None,
        regime: Optional[str] = None
    ) -> List[Dict]:
        """
        Encontra as regras aplicáveis para uma combinação de NCM/CFOP/CST + Contexto (UF/Regime).
        Prioridade: 
        1. Regra com match exato de NCM + Origem + Destino + Regime
        2. Regra com match de NCM + Origem (Nacional)
        3. Regra genérica do regime
        """
        matches = []
        for rule in self._rules_cache:
            rule_ncm = rule.get("ncm")
            rule_cfop = rule.get("cfop")
            rule_cst = rule.get("cst")
            rule_origin = rule.get("origin_uf")
            rule_dest = rule.get("dest_uf")
            rule_regime = rule.get("regime_tributario")
            rule_type = rule.get("rule_type")

            # Filtro de Regime (Se a regra é específica para um regime, deve bater)
            if rule_regime and regime and rule_regime != regime:
                continue

            # Filtro de UF de Origem (Para ICMS/ST)
            if rule_origin and origin_uf and rule_origin != origin_uf:
                continue

            # Filtro de UF de Destino (Para DIFAL/Interestadual)
            if rule_dest and dest_uf and rule_dest != dest_uf:
                continue

            # Cálculo de Especificidade (Score)
            # Prioridade por tamanho do match de NCM (Hierarquia)
            specificity = 0
            if rule_ncm and ncm:
                if ncm == rule_ncm:
                    specificity += 200 # Match exato (8 dígitos)
                elif ncm.startswith(rule_ncm):
                    specificity += 100 + len(rule_ncm) # Match hierárquico (Capítulo/Posição)
                else:
                    continue # NCM não bate
            elif rule_ncm:
                continue # Regra exige NCM mas item não tem
            
            if rule_cfop == cfop: specificity += 50
            if rule_cst == cst: specificity += 30
            if rule_origin == origin_uf: specificity += 20
            if rule_dest == dest_uf: specificity += 20
            if rule_regime == regime: specificity += 10

            matches.append({"rule": rule, "specificity": specificity})

        # Ordena da mais específica para a mais genérica
        matches.sort(key=lambda x: x["specificity"], reverse=True)

        # Retorna as regras encontradas, garantindo que para cada rule_type pegamos a mais específica
        seen_types = set()
        final_rules = []
        for m in matches:
            rtype = m["rule"].get("rule_type")
            if rtype not in seen_types:
                final_rules.append(m["rule"])
                seen_types.add(rtype)

        return final_rules

    def validate_item(
        self, 
        item: Dict[str, Any], 
        origin_uf: Optional[str] = None, 
        dest_uf: Optional[str] = None,
        regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valida um item da NF-e considerando o contexto nacional e tributário.
        """
        self._load_rules()

        ncm = item.get("ncm")
        cfop = item.get("cfop")
        cst = item.get("cst")
        v_prod = item.get("v_prod", 0.0)

        rules = self._find_matching_rules(ncm, cfop, cst, origin_uf=origin_uf, dest_uf=dest_uf, regime=regime)
        alertas = []
        
        # Mapeamento de rule_type para campos do item extraídos pelo XMLParser
        tax_map = {
            "cbs": "v_cbs",
            "ibs": "v_ibs",
            "pis": "v_pis",
            "cofins": "v_cofins",
            "icms": "v_icms",
            "ipi": "v_ipi"
        }

        results_flags = {tax: True for tax in tax_map.keys()}
        tax_values = {tax: 0.0 for tax in tax_map.keys()}
        tax_bases = {f"vbc_{tax}": 0.0 for tax in tax_map.keys()}
        
        suggested_cst = cst
        suggested_cfop = cfop

        for rule in rules:
            rule_type = rule.get("rule_type")
            if rule_type not in tax_map:
                continue

            field_name = tax_map[rule_type]
            expected_rate = float(rule.get("expected_rate", 0))
            
            # Extract suggested CST/CFOP from ICMS or PIS rules
            if rule_type == 'icms' or not suggested_cst:
                rule_cst = rule.get("expected_cst")
                if rule_cst:
                    suggested_cst = str(rule_cst).zfill(2) if len(str(rule_cst)) < 2 else str(rule_cst)
                    
            if rule_type == 'icms' or not suggested_cfop:
                rule_cfop = rule.get("expected_cfop")
                if rule_cfop:
                    suggested_cfop = str(rule_cfop)
            
            # Identificação da Base de Cálculo
            expected_base = v_prod
            base_reduction = float(rule.get("parameters", {}).get("base_reduction", 1.0))
            if base_reduction != 1.0:
                expected_base = round(expected_base * base_reduction, 2)
                
            expected_value = round(expected_base * expected_rate, 2)
            
            tax_values[rule_type] = expected_value
            tax_bases[f"vbc_{rule_type}"] = expected_base
            severity = rule.get("severity", "media")
            category = rule.get("category", "compliance")
            
            actual = item.get(field_name, 0.0)
            diff = abs(actual - expected_value)
            tolerance = float(rule.get("parameters", {}).get("tolerance", 0.05))
            
            if diff > tolerance:
                # Determina se foi um match hierárquico (fallback)
                is_fallback = rule.get("parameters", {}).get("fallback") or (rule.get("ncm") and len(rule.get("ncm", "")) < 8)
                msg_suffix = f" [Base Legal: {rule.get('legal_foundation', 'Legislação Vigente')}]"
                if is_fallback:
                    msg_suffix = f" (Validado por Categoria NCM: {rule.get('ncm')}){msg_suffix}"

                is_opportunity = rule.get("is_opportunity", False)
                results_flags[rule_type] = False
                alertas.append({
                    "tipo": f"{rule_type}_incorreto",
                    "severidade": severity,
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "is_opportunity": is_opportunity,
                    "mensagem": f"{rule_type.upper()} Item {item.get('n_item')}: Esperado R$ {expected_value}, Encontrado R$ {actual} (NCM: {ncm}){msg_suffix}",
                    "valor_esperado": expected_value,
                    "valor_encontrado": actual,
                    "diferenca": round(diff, 2),
                    "legal_foundation": rule.get("legal_foundation")
                })


        # Margear valores calculados e bases de cálculo para o output
        full_tax_info = {**tax_values, **tax_bases}

        return {
            "n_item": item.get("n_item"),
            "ncm": ncm,
            "cfop": cfop,
            "cst": cst,
            "suggested_cfop": suggested_cfop,
            "suggested_cst": suggested_cst,
            "validation_results": results_flags,
            "tax_values": full_tax_info,
            "alertas": alertas
        }

    def validate_nfe(self, nfe_data: Dict[str, Any], empresa_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Valida todos os itens de uma NF-e considerando contexto geográfico e regime.
        """
        self._load_rules()

        itens = nfe_data.get("itens", [])
        origin_uf = nfe_data.get("emitente_uf")
        dest_uf = nfe_data.get("destinatario_uf")
        destinatario_cnpj = nfe_data.get("destinatario_cnpj")
        
        # 1. Tentar obter o regime tributário da empresa
        regime = "lucro_real" # Default seguro
        try:
            admin_client = self.supabase.get_service_client()
            emp_res = None
            
            if empresa_id:
                emp_res = admin_client.table("empresas").select("regime_tributario").eq("id", empresa_id).single().execute()
            elif destinatario_cnpj:
                emp_res = admin_client.table("empresas").select("regime_tributario").eq("cnpj", destinatario_cnpj).single().execute()
            
            if emp_res and emp_res.data:
                regime = emp_res.data.get("regime_tributario", "lucro_real")
        except Exception as e:
            logger.warning(f"RuleEngine: Não foi possível obter o regime: {e}")

        all_alertas = []
        items_results = []
        total_exposure = 0.0

        for item in itens:
            result = self.validate_item(item, origin_uf=origin_uf, dest_uf=dest_uf, regime=regime)
            items_results.append(result)
            all_alertas.extend(result["alertas"])
            total_exposure += sum(a["diferenca"] for a in result["alertas"])

        # Fallback: se não há itens, usar validação de totais (compatibilidade)
        if not itens:
            return self._validate_totals_fallback(nfe_data)

        has_errors = len(all_alertas) > 0
        status = "irregular" if has_errors else "conforme"

        # Consolidar flags de sucesso por tributo
        tax_compliance = {}
        if items_results:
            sample = items_results[0]["validation_results"]
            for tax in sample.keys():
                tax_compliance[f"{tax}_ok"] = all(r["validation_results"].get(tax, True) for r in items_results)

        return {
            "status": status,
            "validation_details": {
                **tax_compliance,
                "total_items": len(itens),
                "items_with_issues": sum(1 for r in items_results if r["alertas"]),
                "total_exposure": round(total_exposure, 2)
            },
            "items_results": items_results,
            "alertas": all_alertas
        }

    def _validate_totals_fallback(self, nfe_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback para notas sem detalhamento de itens (compatibilidade com MVP)."""
        valor_total = nfe_data.get("valor_total", 0.0)
        cbs = nfe_data.get("valor_cbs", 0.0)
        ibs = nfe_data.get("valor_ibs", 0.0)

        # Buscar regras genéricas de CBS e IBS
        cbs_rules = [r for r in self._rules_cache if r.get("rule_type") == "cbs" and not r.get("ncm")]
        ibs_rules = [r for r in self._rules_cache if r.get("rule_type") == "ibs" and not r.get("ncm")]

        cbs_rate = float(cbs_rules[0]["expected_rate"]) if cbs_rules else 0.009
        ibs_rate = float(ibs_rules[0]["expected_rate"]) if ibs_rules else 0.001

        cbs_esperado = round(valor_total * cbs_rate, 2)
        ibs_esperado = round(valor_total * ibs_rate, 2)

        alertas = []
        cbs_ok = abs(cbs - cbs_esperado) <= 0.05
        ibs_ok = abs(ibs - ibs_esperado) <= 0.05

        if not cbs_ok:
            alertas.append({
                "tipo": "cbs_incorreto",
                "severidade": "alta",
                "mensagem": f"CBS Total: Esperado R$ {cbs_esperado}, Encontrado R$ {cbs}",
                "valor_esperado": cbs_esperado,
                "valor_encontrado": cbs,
                "diferenca": round(abs(cbs - cbs_esperado), 2)
            })

        if not ibs_ok:
            alertas.append({
                "tipo": "ibs_incorreto",
                "severidade": "alta",
                "mensagem": f"IBS Total: Esperado R$ {ibs_esperado}, Encontrado R$ {ibs}",
                "valor_esperado": ibs_esperado,
                "valor_encontrado": ibs,
                "diferenca": round(abs(ibs - ibs_esperado), 2)
            })

        status = "irregular" if alertas else ("erro_parse" if valor_total == 0 else "conforme")

        return {
            "status": status,
            "validation_details": {
                "cbs_esperado": cbs_esperado,
                "ibs_esperado": ibs_esperado,
                "cbs_ok": cbs_ok,
                "ibs_ok": ibs_ok
            },
            "items_results": [],
            "alertas": alertas
        }
