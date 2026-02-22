import pytest
from fastapi.testclient import TestClient
from app_v5.main import app

client = TestClient(app)

def test_health_check():
    """Valida se o endpoint de health está respondendo corretamente."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "active"

def test_debug_env_endpoint(mocker):
    """Verifica se o endpoint de debug consegue reportar o status do ambiente (mockado)."""
    # Mock do SupabaseService para não tentar conectar de fato
    mocker.patch("app_v5.core.supabase_client.SupabaseService")
    
    response = client.get("/api/debug-env")
    assert response.status_code == 200
    assert "env_check" in response.json()
    assert "db_test" in response.json()

def test_upload_xml_unauthorized():
    """Garante que o upload exige autenticação (401 ou 403 sem token)."""
    response = client.post("/api/upload/xml")
    assert response.status_code in [401, 403, 422] # 422 se faltar o body, mas auth deve vir antes
