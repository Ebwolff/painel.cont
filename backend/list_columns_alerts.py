import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def list_columns_alerts():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}"
    }
    
    try:
        response = httpx.get(f"{url}/rest/v1/", headers=headers)
        if response.status_code == 200:
            spec = response.json()
            definitions = spec.get("definitions", {})
            nf = definitions.get("alertas_conformidade", {})
            properties = nf.get("properties", {})
            
            print("Colunas de 'alertas_conformidade':")
            for col in sorted(properties.keys()):
                print(f" - {col}")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"🚨 Erro na inspeção: {str(e)}")

if __name__ == "__main__":
    list_columns_alerts()
