import asyncio
import os
from dotenv import load_dotenv
from app.core.supabase_client import SupabaseService

# Load env vars
load_dotenv()

async def seed_company():
    print("Seeding Company (Retry)...")
    service = SupabaseService()
    client = service.get_service_client()
    
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896" 
    
    # Minimal data
    data = {
        "tenant_id": tenant_id,
        "razao_social": "Empresa Teste Debug",
        "cnpj": "12345678000199"
        # Removed 'status' as it caused error
    }
    
    try:
        res = client.table("empresas").insert(data).execute()
        print(f"✅ Company Created: {res.data[0]['id']}")
        return res.data[0]['id']
    except Exception as e:
        print(f"❌ Error creating company: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(seed_company())
