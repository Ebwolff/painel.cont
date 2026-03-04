import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app_v5"))
sys.path.append(os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app_v5.core.supabase_client import SupabaseService

async def check_audit_logs():
    supa = SupabaseService().get_service_client()
    
    print("--- ULTIMOS AUDIT LOGS ---")
    res = supa.table("audit_logs").select("*").order("created_at", desc=True).limit(10).execute()
    if not res.data:
        print("Nenhum log encontrado.")
    else:
        for log in res.data:
            print(f"[{log['created_at']}] {log['action']} - Resource: {log['resource']} (ID: {log['resource_id']})")
            
    print("\n--- DETALHES DO CERTIFICADO ---")
    certs = supa.table("certificados_a1").select("empresa_id, status, updated_at").execute()
    for c in certs.data:
        print(f"Empresa: {c['empresa_id']} | Status: {c['status']} | Atualizado: {c['updated_at']}")

if __name__ == "__main__":
    asyncio.run(check_audit_logs())
