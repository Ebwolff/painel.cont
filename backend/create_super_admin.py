import asyncio
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Carregar variáveis de ambiente
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Precisa da chave de serviço para criar usuários sem confirmação e ignorar RLS

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não encontrados no .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def create_super_admin():
    email = input("Email do Super Admin: ").strip()
    password = input("Senha do Super Admin: ").strip()

    if len(password) < 6:
        print("❌ A senha deve ter pelo menos 6 caracteres.")
        return

    print(f"🔄 Verificando usuário {email}...")

    # 1. Tentar buscar usuário existente, se a biblioteca permitir (admin list users)
    # Como auth.admin.list_users() pode não ser direto, vamos tentar criar e tratar erro, ou criar via sign_in dummy?
    # Melhor: Usar create_user e tratar erro se já existir.
    
    user_id = None
    
    try:
        # Tenta criar o usuário (admin api cria e confirma email automaticamente)
        user_attributes = {
            "email": email,
            "password": password,
            "email_confirm": True
        }
        user = supabase.auth.admin.create_user(user_attributes)
        user_id = user.user.id
        print(f"✅ Usuário criado com sucesso! ID: {user_id}")
        
    except Exception as e:
        error_msg = str(e)
        # Catch various forms of "User already exists" error
        if "already been registered" in error_msg or "already exists" in error_msg:
            print("⚠️ Usuário já existe. Atualizando senha e promovendo...")
            
            try:
                # LIST ALL users to find the ID
                # Pagination loop might be needed in prod, but for now fetching first page
                users_response = supabase.auth.admin.list_users()
                for u in users_response:
                     if u.email == email:
                         user_id = u.id
                         break
                
                if user_id:
                    supabase.auth.admin.update_user_by_id(user_id, {"password": password})
                    print("✅ Senha atualizada.")
                else:
                    print("❌ Não foi possível encontrar o ID do usuário existente para atualizar a senha.")
                    print("Tente deletar o usuário no painel do Supabase e rodar novamente.")
                    return

            except Exception as inner_e:
                print(f"❌ Erro ao tentar atualizar usuário existente: {inner_e}")
                return
        else:
            print(f"❌ Erro ao criar usuário: {e}")
            return


    if user_id:
        print("🔄 Promovendo a SUPER ADMIN no banco de dados...")
        
        # 2. Atualizar tabela profiles
        try:
             # Update profile role
             supabase.table("profiles").update({
                 "role": "super_admin",
                 "permissions": {
                    "can_manage_tenants": True,
                    "can_manage_users": True,
                    "can_view_metrics": True
                }
             }).eq("id", user_id).execute()
             
             print("👑 SUCESSO! O usuário agora é um Super Admin.")
             print(f"📧 Email: {email}")
             print("🔑 Senha: (definida por você)")
             print("\nAgora faça login em /admin")
             
        except Exception as e:
            print(f"❌ Erro ao atualizar tabela profiles: {e}")

if __name__ == "__main__":
    asyncio.run(create_super_admin())
