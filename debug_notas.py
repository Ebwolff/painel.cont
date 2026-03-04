import os
import asyncio
from app_v5.core.supabase_client import SupabaseService

async def debug_data():
    supabase = SupabaseService()
    admin_client = supabase.get_service_client()
    
    # 1. Total notas in the system
    res_total = admin_client.table("notas_fiscais").select("id", count="exact").execute()
    print(f"Total notas in system: {res_total.count}")
    
    # 2. Sample notas with their CNPJs
    res_sample = admin_client.table("notas_fiscais").select("numero, emitente_cnpj, destinatario_cnpj, tenant_id, empresa_id").limit(20).execute()
    print("\nSample Notas:")
    for n in res_sample.data or []:
        print(f"Nota {n.get('numero')}: Emitente={n.get('emitente_cnpj')}, Destinatario={n.get('destinatario_cnpj')}, Tenant={n.get('tenant_id')}, Empresa={n.get('empresa_id')}")
        
    # 3. Companies and their CNPJs
    res_comp = admin_client.table("empresas").select("id, razao_social, cnpj, tenant_id").execute()
    print("\nCompanies in system:")
    for c in res_comp.data or []:
        print(f"ID: {c.get('id')}, Razão: {c.get('razao_social')}, CNPJ: {c.get('cnpj')}, Tenant: {c.get('tenant_id')}")

    # 4. Check if we have any mismatch (special characters, etc)
    if res_comp.data and res_sample.data:
        company_cnpjs = [c.get('cnpj') for c in res_comp.data]
        for n in res_sample.data:
            if n.get('emitente_cnpj') in company_cnpjs:
                print(f"MATCH (Saída): Nota {n.get('numero')} EMI {n.get('emitente_cnpj')} exists in companies")
            if n.get('destinatario_cnpj') in company_cnpjs:
                print(f"MATCH (Entrada): Nota {n.get('numero')} DEST {n.get('destinatario_cnpj')} exists in companies")

if __name__ == "__main__":
    asyncio.run(debug_data())
