import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def list_columns():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}"
    }
    
    # O PostgREST expõe metadados na raiz
    print(f"Inspecionando colunas de 'notas_fiscais' via OpenAPI...")
    try:
        # Pede o esquema OpenAPI para ver o que a API "enxerga"
        response = httpx.get(f"{url}/rest/v1/", headers=headers)
        if response.status_code == 200:
            spec = response.json()
            definitions = spec.get("definitions", {})
            nf = definitions.get("notas_fiscais", {})
            properties = nf.get("properties", {})
            
            if properties:
                print("Colunas encontradas pela API:")
                for col in sorted(properties.keys()):
                    print(f" - {col}")
            else:
                print("🚨 Nenhuma coluna encontrada para 'notas_fiscais' na definição da API.")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"🚨 Erro na inspeção: {str(e)}")

if __name__ == "__main__":
    list_columns()
