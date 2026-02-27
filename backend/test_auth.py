import os
import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.getenv('SUPABASE_URL')
key_admin = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
key_anon = os.getenv('SUPABASE_KEY')

client_admin = create_client(url, key_admin)
client_anon = create_client(url, key_anon)

try:
    # Auto-create user
    email = "testproxy@admin.com"
    pwd = "password123"
    try:
        client_admin.auth.admin.create_user({"email": email, "password": pwd, "email_confirm": True})
        print("User created.")
    except Exception as create_err:
        print(f"Passed user creation: {create_err}")

    res = client_anon.auth.sign_in_with_password({'email': email, 'password': pwd})
    token = res.session.access_token
    print(f"Token obtained!")

    headers = {'Authorization': f'Bearer {token}'}
    r = httpx.get('http://127.0.0.1:8000/api/dashboard/current-company', headers=headers)
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    import traceback
    print("Error during test:")
    traceback.print_exc()
