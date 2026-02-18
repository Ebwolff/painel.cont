import asyncio
import os
from dotenv import load_dotenv
from app.core.supabase_client import SupabaseService

# Load env vars
load_dotenv()

async def debug_create_monitor():
    print("Debugging Monitor Creation...")
    service = SupabaseService()
    admin_client = service.get_service_client()
    
    # 1. Get Company
    companies = admin_client.table("empresas").select("id").limit(1).execute()
    if not companies.data:
        print("❌ CRITICAL: No companies found to link.")
        return
    
    company_id = companies.data[0]['id']
    print(f"Using Company ID: {company_id}")
    
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896"
    test_email = "monitor.debug@test.com"
    test_pass = "password123"
    
    # Cleanup
    users = admin_client.auth.admin.list_users()
    for u in users:
        if u.email == test_email:
            admin_client.auth.admin.delete_user(u.id)
            print("Deleted old debug user.")

    # 2. Create Auth User
    print("Creating Auth User...")
    try:
        auth_res = admin_client.auth.admin.create_user({
            "email": test_email,
            "password": test_pass,
            "email_confirm": True,
            "user_metadata": {"full_name": "Monitor Debug"}
        })
        user_id = auth_res.user.id
        print(f"User Created: {user_id}")
        
        # 3. Update Profile (simulate backend logic)
        print("Updating Profile with empresa_id...")
        update_data = {
            "tenant_id": tenant_id,
            "role": "monitor",
            "nome": "Monitor Debug",
            "empresa_id": company_id
        }
        
        res = admin_client.table("profiles").update(update_data).eq("id", user_id).execute()
        print(f"Profile Update Result: {res.data}")
        
        if res.data and res.data[0].get('empresa_id') == company_id:
            print("✅ SUCCESS: Monitor user created and linked.")
        else:
            print("❌ FAILURE: Profile updated but data mismatches or empty.")
            
    except Exception as e:
        print(f"❌ FAILURE during creation flow: {e}")

if __name__ == "__main__":
    asyncio.run(debug_create_monitor())
