import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

def debug_api():
    # 1. Login
    try:
        print(f"Login attempt to {BASE_URL}/auth/token...")
        # A rota de token pode ser /auth/token ou /token, vamos verificar o main.py depois se falhar
        # Mas pelo contexto, usamos /auth/token no frontend? Não, usually /token via OAuth2, but let's see.
        # Actually, let's look at `security.py` or `users.py`? 
        # Wait, I don't recall seeing a login endpoint in the previous files.
        # Let's assume standard FastAPI OAuth2 path: /token
        
        # But wait, the frontend calls `supabase.auth.signInWithPassword`.
        # The backend receives the token in the header.
        
        # So I need to simulate a request with a valid Supabase token.
        # I can get a token by using the Supabase Client directly in Python to sign in.
        
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        supabase = create_client(url, key)
        
        email = "carlos@test.com"
        password = "newpassword123" # Updated via admin script
        
        print(f"Signing in as {email}...")
        session = supabase.auth.sign_in_with_password({"email": email, "password": password})
        token = session.session.access_token
        print("Login successful! Token acquired.")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Call /api/alerts
        print("\nCalling GET /api/alerts/ ...")
        resp = requests.get(f"{BASE_URL}/api/alerts/", headers=headers)
        
        print(f"Status Code: {resp.status_code}")
        try:
            data = resp.json()
            print("Response JSON (first 500 chars):")
            print(str(data)[:500])
            
            if isinstance(data, dict) and "error" in data:
                print("\n[ERROR DETECTED IN RESPONSE]")
                print(data)
            elif isinstance(data, list):
                print(f"\n[SUCCESS] Returned list of {len(data)} items.")
                if len(data) > 0:
                    print("Sample item keys:", data[0].keys())
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
            print("Raw text:", resp.text[:500])

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    debug_api()
