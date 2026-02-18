import asyncio
from dotenv import load_dotenv
from app.core.supabase_client import SupabaseService

# Load env vars
load_dotenv()

async def list_companies():
    service = SupabaseService()
    client = service.get_service_client()
    
    print("Listing companies...")
    try:
        res = client.table("empresas").select("id, razao_social").execute()
        if not res.data:
            print("⚠️  No companies found.")
        else:
            print(f"✅ Found {len(res.data)} companies:")
            for c in res.data:
                print(f"   - {c['razao_social']} ({c['id']})")
                
    except Exception as e:
        print(f"Error listing companies: {e}")

if __name__ == "__main__":
    asyncio.run(list_companies())
