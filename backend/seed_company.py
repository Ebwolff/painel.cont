import asyncio
import os
from dotenv import load_dotenv
from app.core.supabase_client import SupabaseService
from app.core.security import get_current_token

# Load env vars
load_dotenv()

async def seed_company():
    print("Seeding Company...")
    service = SupabaseService()
    # We need to be logged in as a Tenant Admin to create a company usually, 
    # but for seeding we can use service role and manually set tenant_id.
    client = service.get_service_client()
    
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896" # Escritório Modelo known ID
    
    data = {
        "tenant_id": tenant_id,
        "razao_social": "Empresa Teste Debug",
        "cnpj": "12345678000199",
        "status": "active"
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
