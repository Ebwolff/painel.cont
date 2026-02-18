import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_integrity():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    print("--- Detalhando Alerta Corrompido ---")
    res = supabase.table("alertas_conformidade").select("*").execute()
    if not res.data:
        print("Ué? count_db viu 1, mas select(*) viu 0. Problema de cache ou transação?")
        return
        
    alerta = res.data[0]
    print(f"Alerta ID: {alerta['id']}")
    print(f"Tenant ID do Alerta: {alerta['tenant_id']}")
    print(f"Nota Fiscal ID no Alerta: {alerta['nota_fiscal_id']}")
    
    # Verificar se a nota existe
    if alerta['nota_fiscal_id']:
        res_nota = supabase.table("notas_fiscais").select("*").eq("id", alerta['nota_fiscal_id']).execute()
        if res_nota.data:
            print(f"✅ Nota Fiscal encontrada. Tenant ID da Nota: {res_nota.data[0]['tenant_id']}")
            if res_nota.data[0]['tenant_id'] != alerta['tenant_id']:
                print(f"🚨 DISCREPÂNCIA: Alerta e Nota têm tenant_ids diferentes!")
        else:
            print(f"🚨 NOTA FISCAL NÃO ENCONTRADA (ID: {alerta['nota_fiscal_id']})")

if __name__ == "__main__":
    check_integrity()
