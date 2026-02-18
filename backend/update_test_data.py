import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def update_test_alert():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    alert_id = "b6ca7b78-2128-424f-82ee-ef86a9067fa9" # From debug logs
    
    print(f"Updating alert {alert_id} with realistic values...")
    
    payload = {
        "valor_esperado": 1500.00,
        "valor_encontrado": 1250.00,
        "diferenca": 250.00,
        "mensagem": "Divergência de alíquota CBS (Esperado 1500.00 vs Encontrado 1250.00)"
    }
    
    try:
        res = supabase.table("alertas_conformidade").update(payload).eq("id", alert_id).execute()
        if res.data:
            print("Success! Updated data:", res.data[0])
        else:
            print("No data returned. Check if ID exists.")
            
    except Exception as e:
        print(f"Error updating alert: {e}")

if __name__ == "__main__":
    update_test_alert()
