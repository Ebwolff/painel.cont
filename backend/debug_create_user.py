import asyncio
from app.core.supabase_client import SupabaseService
import sys

async def mock_create_user():
    service = SupabaseService()
    admin_client = service.get_service_client()
    
    email = "ir.carlos@test.com"
    password = "password123" # Or whatever user used, but 123456 is likely
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896"
    nome = "Carlos Debug 2"
    role = "contador"
    
    print(f"Attempting to create user: {email}")
    
    try:
        # 1. Create Auth User
        print("1. Creating Auth User...")
        auth_res = admin_client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        # Check for error in response object if it doesn't raise exception
        if hasattr(auth_res, 'user') and auth_res.user:
            print(f"Auth user created with ID: {auth_res.user.id}")
            new_user_id = auth_res.user.id
        else:
            print(f"Auth creation failed? Response: {auth_res}")
            return

        # 2. Update Profile
        print("2. Updating Profile...")
        profile_update = {
            "tenant_id": tenant_id,
            "nome": nome,
            "role": role
        }
        res = admin_client.table("profiles").update(profile_update).eq("id", new_user_id).execute()
        print(f"Profile update response: {res}")
        
    except Exception as e:
        print(f"CAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(mock_create_user())
