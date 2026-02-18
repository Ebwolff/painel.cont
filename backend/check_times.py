import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def check_timestamps():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    now = datetime.now()
    data_limite = (now - timedelta(days=30)).isoformat()
    
    print(f"Hora atual do sistema: {now.isoformat()}")
    print(f"Data limite (30 dias): {data_limite}")
    
    res = supabase.table("notas_fiscais").select("id, created_at, status").execute()
    print("\n--- Notas Encontradas ---")
    for nota in res.data:
        print(f"ID: {nota['id']} | Created: {nota['created_at']} | Status: {nota['status']}")
        # Comparação manual
        created_dt = datetime.fromisoformat(nota['created_at'].replace('Z', '+00:00'))
        is_included = nota['created_at'] >= data_limite
        print(f"  > Estaria no dashboard? {'SIM' if is_included else 'NÃO'}")

if __name__ == "__main__":
    check_timestamps()
