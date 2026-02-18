import asyncio
from dotenv import load_dotenv
from app.core.supabase_client import SupabaseService

# Load env vars
load_dotenv()

async def check_migration():
    service = SupabaseService()
    client = service.get_service_client()
    
    print("Checking if 'empresa_id' column exists in 'profiles'...")
    try:
        # Try to select the column from profiles.
        # If column doesn't exist, this query will fail.
        res = client.table("profiles").select("empresa_id").limit(1).execute()
        print("✅ SUCCESS: 'empresa_id' column exists.")
        
        # Check if user role 'monitor' is accepted in check (can't easily check check constraint via API select)
        # But column existence is the main blocker.
        
    except Exception as e:
        print(f"❌ FAILURE: 'empresa_id' column likely missing. Error: {e}")
        print("PLEASE RUN THE SQL MIGRATION IN SUPABASE EDITOR.")

if __name__ == "__main__":
    asyncio.run(check_migration())
