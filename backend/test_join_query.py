import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def test_backend_query():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Testando Query do Backend (Join com Empresas) ---")
    try:
        # Esta é a query exata do alerts.py:46
        res = supabase.table("alertas_conformidade").select("*, notas_fiscais(numero, chave_acesso), empresas(razao_social)").execute()
        print("Sucesso Inesperado (Join funcionou?):")
        print(json.dumps(res.data, indent=2))
    except Exception as e:
        print(f"❌ ERRO IDENTIFICADO: {str(e)}")

    print("\n--- Teste 2: Join via Notas Fiscais ---")
    try:
        # Tentativa correta se o link for via notas
        res = supabase.table("alertas_conformidade").select("*, notas_fiscais(numero, chave_acesso, empresas(razao_social))").execute()
        print("✅ Join via Notas funcionou:")
        print(json.dumps(res.data, indent=2))
    except Exception as e:
        print(f"❌ Erro Teste 2: {str(e)}")

if __name__ == "__main__":
    test_backend_query()
