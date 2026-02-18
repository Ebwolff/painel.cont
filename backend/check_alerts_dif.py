import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_alerts():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    tenant_id = "6dbc5f1f-da52-4ea8-8105-611b243649a6" # Taless
    
    print(f"--- Checking Alerts for Tenant: {tenant_id} ---")
    res = supabase.table("alertas_conformidade").select("id, tipo, mensagem, diferenca, valor_esperado, valor_encontrado").eq("tenant_id", tenant_id).execute()
    
    if res.data:
        for a in res.data:
            print(f"Alerta ID: {a['id']}")
            print(f"  Tipo: {a['tipo']}")
            print(f"  Mensagem: {a['mensagem']}")
            print(f"  Diferença: {a['diferenca']} (Type: {type(a['diferenca'])})")
            print(f"  Esperado: {a['valor_esperado']}")
            print(f"  Encontrado: {a['valor_encontrado']}")
            print("-" * 30)
    else:
        print("No alerts found.")

if __name__ == "__main__":
    check_alerts()
