import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def debug_data():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    email = "carlos@test.com"
    print(f"--- Diagnóstico para {email} ---")
    
    # 1. Obter UUID do Auth
    auth_users = supabase.auth.admin.list_users()
    carlos_auth = next((u for u in auth_users if u.email == email), None)
    
    if not carlos_auth:
        print("Usuário não encontrado no Auth!")
        return
    
    user_id = carlos_auth.id
    print(f"User ID (Auth): {user_id}")
    
    # 2. Obter Perfil e Tenant
    res_profile = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    if not res_profile.data:
        print(f"Nenhum perfil encontrado para ID {user_id}")
        return
        
    profile = res_profile.data
    tenant_id = profile.get('tenant_id')
    print(f"Perfil encontrado: {profile}")
    print(f"Tenant ID: {tenant_id}")
    
    if not tenant_id:
        print("ALERTA: Tenant ID é Nulo!")
        return

    # 3. Contagem de Tabelas por Tenant
    print(f"\n--- Dados vinculados ao Tenant {tenant_id} ---")
    
    # Empresas
    empresas = supabase.table("empresas").select("id, razao_social", count="exact").eq("tenant_id", tenant_id).execute()
    print(f"Empresas: {empresas.count} encontrados")
    if empresas.data:
        print(f"  Exemplos: {[e['razao_social'] for e in empresas.data[:3]]}")
    else:
        print("  AVISO: Nenhuma empresa encontrada.")

    # Notas Fiscais
    notas = supabase.table("notas_fiscais").select("id", count="exact").eq("tenant_id", tenant_id).execute()
    print(f"Notas Fiscais: {notas.count} encontrados")
    
    # Alertas
    alertas = supabase.table("alertas_conformidade").select("id", count="exact").eq("tenant_id", tenant_id).execute()
    print(f"Alertas: {alertas.count} encontrados")
    
    # Alertas sem Tenant ID (Órfãos?)
    alertas_orf = supabase.table("alertas_conformidade").select("id", count="exact").is_("tenant_id", "null").execute()
    print(f"Alertas SEM Tenant ID (Órfãos): {alertas_orf.count}")

    if alertas.count == 0 and alertas_orf.count > 0:
        print("\nDIAGNÓSTICO: Existem alertas órfãos mas nenhum vinculado ao tenant. O vínculo está quebrado.")

if __name__ == "__main__":
    debug_data()
