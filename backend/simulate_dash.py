import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def simulate_dashboard():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Simular UID do Carlos
    user_id = "78351bb6-0347-4fc5-99c0-8874720036c8"
    
    print(f"--- Simulação Dashboard para Usuário {user_id} ---")
    
    # 1. Buscar Perfil (Simulando o que o router faz)
    profile_res = supabase.table("profiles").select("role, empresa_id, tenant_id").eq("id", user_id).single().execute()
    profile = profile_res.data
    print(f"Perfil encontrado: {json.dumps(profile, indent=2)}")
    
    # 2. Configurar window de tempo
    data_limite = (datetime.now() - timedelta(days=30)).isoformat()
    print(f"Buscando notas desde: {data_limite}")
    
    # 3. Executar Queries (Usando service_role para ver se existem dados primeiro)
    # No router, usamos o token do usuário. Aqui usamos service_role para confirmar se o dado EXISTE fisicamente.
    total_res = supabase.table("notas_fiscais").select("id, tenant_id, created_at", count="exact").execute()
    print(f"\nTotal físico de notas no banco: {total_res.count}")
    
    # 4. Filtrar como o router faria
    tenant_id = profile.get("tenant_id")
    filtered_res = supabase.table("notas_fiscais")\
        .select("id", count="exact")\
        .eq("tenant_id", tenant_id)\
        .gte("created_at", data_limite)\
        .execute()
    
    print(f"Total de notas para o tenant {tenant_id} nos últimos 30 dias: {filtered_res.count}")

    # 5. Verificar Alertas
    alert_res = supabase.table("alertas_conformidade")\
        .select("id", count="exact")\
        .eq("tenant_id", tenant_id)\
        .execute()
    print(f"Total de alertas para o tenant: {alert_res.count}")

if __name__ == "__main__":
    simulate_dashboard()
