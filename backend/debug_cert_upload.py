import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app_v5.routers.certificates import upload_certificate
from fastapi import UploadFile
import io

class MockUploadFile(UploadFile):
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content
        # Simulating file read
        self.file = io.BytesIO(content)

    async def read(self, size: int = -1):
        return self._content

async def run_upload():
    print("Mocking certificate upload...")
    
    # Needs valid pfx content for `_read_cert_expiry` to not fail
    # Wait, if `_read_cert_expiry` fails, it raises 422.
    # The previous code (with double encode) passed `_read_cert_expiry` because it happens BEFORE encryption!
    # So `_read_cert_expiry` is not the new issue.
    # Is it the base64 / encryption part? Let's just mock the endpoints or call the DB directly.
    
    from app_v5.core.supabase_client import SupabaseService
    import base64
    
    supa = SupabaseService()
    
    try:
        content = b"fake_pfx_content_1234567890"
        password = "test_password"
        
        cert_b64_str = base64.b64encode(content).decode("utf-8")
        print(f"B64 str len: {len(cert_b64_str)}")
        
        cert_encrypted = supa.encrypt_data(cert_b64_str)
        print(f"Encrypted len: {len(cert_encrypted)}")
        
        senha_encrypted = supa.encrypt_data(password)
        print(f"Pass Encrypted len: {len(senha_encrypted)}")
        
        print("Success! No crash during encryption.")
    except Exception as e:
        print(f"CRASH: {e}")

if __name__ == "__main__":
    asyncio.run(run_upload())
