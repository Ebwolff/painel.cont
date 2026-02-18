import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_session_sync():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Carlos Email
    email = "carlos@test.com"
    
    print(f"--- Verificando Sincronia de IDs para {email} ---")
    
    # 1. Buscar no Auth (via admin API)
    auth_users = supabase.auth.admin.list_users()
    carlos_auth = next((u for u in auth_users if u.email == email), None)
    
    if not carlos_auth:
        print("ERRO: Usuário não encontrado no Auth!")
        return

    auth_id = carlos_auth.id
    print(f"ID no Auth (JWT): {auth_id}")
    
    # 2. Buscar no Profiles
    profile = supabase.table("profiles").select("*").eq("id", auth_id).execute()
    
    if not profile.data:
        print(f"ERRO CRÍTICO: Não existe perfil para o ID {auth_id} na tabela profiles!")
        # Vamos ver se existe algum perfil com esse e-mail mas ID diferente
        all_profiles = supabase.table("profiles").select("*").execute()
        print("\nTodos os Perfis no Banco:")
        print(json.dumps(all_profiles.data, indent=2))
    else:
        print(f"Perfil encontrado: {json.dumps(profile.data[0], indent=2)}")
        print("Sincronia OK!")

if __name__ == "__main__":
    check_session_sync()
