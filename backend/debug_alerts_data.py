import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()

def debug_data():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    tenant_id = "6dbc5f1f-da52-4ea8-8105-611b243649a6" # Taless
    
    print(f"--- Diagnóstico de Dados para Tenant: {tenant_id} ---")

    # 1. Buscar Alertas com Joins
    res = supabase.table("alertas_conformidade").select("*, notas_fiscais(id, numero, empresa_id, empresas(razao_social))").eq("tenant_id", tenant_id).execute()
    
    if res.data:
        for a in res.data:
            nota = a.get('notas_fiscais')
            empresa = nota.get('empresas') if nota else None
            razao_social = empresa.get('razao_social') if empresa else "NULL"
            
            print(f"Alerta ID: {a['id']}")
            print(f"  Mensagem: {a['mensagem'][:40]}...")
            print(f"  Nota Fiscal ID: {a.get('nota_fiscal_id')}")
            if nota:
                print(f"  Nota Numero: {nota.get('numero')}")
                print(f"  Nota Empresa ID: {nota.get('empresa_id')}")
                print(f"  Empresa Razão Social (Join): {razao_social}")
            else:
                print("  [ERRO] Nota Fiscal não encontrada para este alerta.")
            print("-" * 30)
    else:
        print("Nenhum alerta encontrado para este tenant.")

if __name__ == "__main__":
    debug_data()
