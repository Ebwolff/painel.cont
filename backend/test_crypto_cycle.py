import asyncio
import os
import sys
import base64
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

load_dotenv()

from app_v5.core.supabase_client import SupabaseService
from app_v5.services.sefaz_client import SefazClient

async def run_full_cycle():
    print("--- INICIANDO CICLO COMPLETO DE TESTE ---")
    supa = SupabaseService()
    
    # 1. Simular UPLOAD (Encriptar)
    # Criar um PFX fake pequenininho apenas para testar a encriptacao/decriptacao
    fake_pfx_content = b"fake_pfx_bytes_1234567890" 
    fake_password = "senha_super_secreta"
    
    print("\n[1] ENCRIPTANDO DADOS (Simulando Upload)...")
    cert_b64_str = base64.b64encode(fake_pfx_content).decode("utf-8")
    cert_encrypted = supa.encrypt_data(cert_b64_str)
    senha_encrypted = supa.encrypt_data(fake_password)
    
    print(f"  > PFX Original Length: {len(fake_pfx_content)}")
    print(f"  > B64 Length: {len(cert_b64_str)}")
    print(f"  > Encrypted B64 Length: {len(cert_encrypted)}")
    print(f"  > Encrypted Pass Length: {len(senha_encrypted)}")
    
    # 2. Simular SYNC (Decriptar)
    print("\n[2] DECRIPTANDO DADOS (Simulando Sefaz Sync)...")
    
    cert_b64_decrypted = supa.decrypt_data(cert_encrypted)
    senha_decrypted = supa.decrypt_data(senha_encrypted)
    
    print(f"  > Decrypted B64 Length: {len(cert_b64_decrypted)}")
    
    if cert_b64_decrypted == "[ERRO_AO_DESCRIPTOGRAFAR]":
        print("❌ ERRO FATAL: Falha ao descriptografar. A MASTER_ENCRYPTION_KEY é inválida ou os dados corromperam.")
        return
        
    try:
        # Corrigir padding se necessario
        pad = len(cert_b64_decrypted) % 4
        if pad:
            cert_b64_decrypted += "=" * (4 - pad)
            
        pfx_bytes_restored = base64.b64decode(cert_b64_decrypted)
        
        print("✅ Dados restaurados com sucesso!")
        print(f"  > Senha original == restaurada? {fake_password == senha_decrypted}")
        print(f"  > PFX original == restaurado? {fake_pfx_content == pfx_bytes_restored}")
        
    except Exception as e:
        print(f"❌ ERRO no Base64 Decode: {e}")

if __name__ == "__main__":
    asyncio.run(run_full_cycle())
