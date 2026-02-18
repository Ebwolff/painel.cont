import asyncio
import os
from dotenv import load_dotenv
from app.core.supabase_client import SupabaseService

# Load env vars
load_dotenv()

async def verify_user_management():
    print("Starting User Management Verification...")
    
    # Setup
    service = SupabaseService()
    admin_client = service.get_service_client()
    
    # 1. Login/Get Token (We'll use service key for admin actions simulation as if we are the user)
    # Actually, the endpoints use 'verify_super_admin' which checks the token. 
    # To test the API properly, we should use `requests` or `httpx` against the running server.
    # But for quick logic verification, we can call the supabase methods directly or use the service client 
    # to mimic what the endpoint does.
    # HOWEVER, to test the ROUTER logic (permissions), we need a valid token.
    
    # Let's use the service client to get a session for eberscaow@gmail.com
    # Sign in with password
    try:
        print("1. Signing in as Super Admin...")
        auth_res = admin_client.auth.sign_in_with_password({
            "email": "eberscaow@gmail.com",
            "password": "password123" # Assuming this is the password from previous context or seed
        })
        
        if not auth_res.user:
            print("Failed to sign in. Cannot verify permissions logic.")
            return

        token = auth_res.session.access_token
        print("Logged in successfully.")
        
    except Exception as e:
        print(f"Login failed: {e}")
        # If login fails (maybe password changed), we might need to skip full API test 
        # and just test the DB logic with service role.
        print("Proceeding with Service Role to test Data Logic directly...")
        token = None

    # Test Data
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896" # Escritório Modelo
    test_email = "api.test.user@example.com"
    test_pass = "password123"
    
    # CLEANUP FIRST
    print("Cleaning up potential debris...")
    users = admin_client.auth.admin.list_users()
    for u in users:
        if u.email == test_email:
            admin_client.auth.admin.delete_user(u.id)
            print(f"Deleted old test user {u.id}")

    # 2. CREATE (mimicking router.post /admin/users)
    print("2. Testing CREATE...")
    # Create Auth
    user_res = admin_client.auth.admin.create_user({
        "email": test_email,
        "password": test_pass,
        "email_confirm": True
    })
    new_user_id = user_res.user.id
    print(f"Created Auth User: {new_user_id}")
    
    # Update Profile (Router Logic)
    admin_client.table("profiles").update({
        "tenant_id": tenant_id,
        "nome": "API Test User",
        "role": "contador"
    }).eq("id", new_user_id).execute()
    print("Updated Profile.")
    
    # 3. VERIFY CREATE
    p_res = admin_client.table("profiles").select("*").eq("id", new_user_id).single().execute()
    print(f"Profile after create: {p_res.data['nome']} - {p_res.data['role']}")
    
    # 4. UPDATE (mimicking router.put /admin/users/{id})
    print("4. Testing UPDATE...")
    admin_client.table("profiles").update({
        "nome": "API Test User EDITED",
        "role": "admin"
    }).eq("id", new_user_id).execute()
    
    p_res = admin_client.table("profiles").select("*").eq("id", new_user_id).single().execute()
    print(f"Profile after update: {p_res.data['nome']} - {p_res.data['role']}")
    
    if p_res.data['nome'] != "API Test User EDITED":
        print("❌ UPDATE FAILED")
    else:
        print("✅ UPDATE SUCCESS")
        
    # 5. DELETE (mimicking router.delete /admin/users/{id})
    print("5. Testing DELETE...")
    del_res = admin_client.auth.admin.delete_user(new_user_id)
    print(f"Delete Result: {del_res}")
    
    # Verify gone
    check_res = admin_client.table("profiles").select("*").eq("id", new_user_id).execute()
    if not check_res.data:
        print("✅ DELETE SUCCESS (Profile gone via cascade or logic)")
    else:
        print(f"❌ DELETE WARNING: Profile still exists? {check_res.data}")
        # Manually cleanup if needed
        admin_client.table("profiles").delete().eq("id", new_user_id).execute()

if __name__ == "__main__":
    asyncio.run(verify_user_management())
