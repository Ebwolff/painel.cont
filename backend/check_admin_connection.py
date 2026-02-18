import os
from dotenv import load_dotenv
from supabase import create_client

# Force load .env
load_dotenv()

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print(f"URL: {URL}")
print(f"KEY: {KEY[:10]}..." if KEY else "KEY: None")

if not KEY:
    print("❌ Service Key NOT found in env!")
    exit(1)

try:
    print("🔄 Connecting with Service Key...")
    client = create_client(URL, KEY)
    
    print("🔄 Fetching tenants...")
    res = client.table("tenants").select("*").execute()
    
    print(f"✅ Success! Found {len(res.data)} tenants.")
    print(res.data)

except Exception as e:
    print(f"❌ Error connecting: {e}")
