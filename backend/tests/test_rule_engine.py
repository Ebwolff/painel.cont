import pytest
from app_v5.services.rule_engine import RuleEngineService

def test_find_matching_rules_specificity(mocker):
    """Valida se o motor de regras seleciona a regra mais específica (Ranking)."""
    # Mock do SupabaseService para não carregar do banco real
    mock_supabase = mocker.patch("app_v5.services.rule_engine.SupabaseService")
    
    engine = RuleEngineService()
    engine._rules_cache = [
        {"id": "1", "ncm": "1234", "rule_type": "cbs", "expected_rate": 0.009, "active": True}, # Genérica (capítulo)
        {"id": "2", "ncm": "12345678", "rule_type": "cbs", "expected_rate": 0.05, "active": True}, # Específica
        {"id": "3", "ncm": "12345678", "rule_type": "ibs", "expected_rate": 0.01, "active": True}, # Outro tipo
    ]
    engine._cache_loaded = True
    
    # Match para CBS
    rules = engine._find_matching_rules(ncm="12345678", cfop="5102", cst="00")
    
    # Deve encontrar 2 para CBS (ID 1 e 2) e 1 para IBS (ID 3)
    # Mas a função retorna apenas a mais específica por rule_type
    assert len(rules) == 2
    
    cbs_rule = next(r for r in rules if r["rule_type"] == "cbs")
    assert cbs_rule["id"] == "2" # A mais específica (8 dígitos) ganha da de 4 dígitos

def test_validate_item_with_alerts():
    """Verifica se o validador gera alertas quando o valor diverge da regra."""
    engine = RuleEngineService()
    engine._rules_cache = [
        {"id": "r1", "rule_type": "cbs", "expected_rate": 0.09, "active": True, "name": "CBS Teste", "severity": "alta"}
    ]
    engine._cache_loaded = True
    
    item = {
        "n_item": 1,
        "ncm": "12345678",
        "v_prod": 1000.00,
        "v_cbs": 10.00 # Devia ser 90.00 (9%)
    }
    
    result = engine.validate_item(item)
    
    assert result["validation_results"]["cbs"] is False
    assert len(result["alertas"]) == 1
    assert result["alertas"][0]["tipo"] == "cbs_incorreto"
    assert result["alertas"][0]["diferenca"] == 80.00 # 90 - 10
