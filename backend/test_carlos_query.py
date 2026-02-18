import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def test_carlos_join():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    # Carlos Tenant ID
    tenant_id = "e34608e1-c7c1-4acf-afa9-63bae1521896"
    
    print(f"--- Teste de Joins para Tenant {tenant_id} ---")

    # 1. Simular o que o PostgREST faz (usando service_role para ver se a estrutura está ok)
    try:
        # Alertas com notas e empresas
        query = supabase.table("alertas_conformidade").select("*, notas_fiscais(numero, empresas(razao_social))").eq("tenant_id", tenant_id)
        res = query.execute()
        print(f"Sucesso na query física: {len(res.data)} registros encontrados.")
        if res.data:
            sample = res.data[0]
            print("Amostra Nota Fiscal vinculada:", sample.get("notas_fiscais"))
    except Exception as e:
        print(f"Erro físico na query de join: {e}")

    # 2. Investigar permissões de SELECT nas tabelas de apoio
    # Se o RLS de notas_fiscais usar get_my_tenant(), vamos ver se ele retorna o que esperamos.
    # Como não podemos logar como Carlos aqui, vamos checar se as tabelas têm o tenant_id correto.
    
    notes = supabase.table("notas_fiscais").select("id, tenant_id, empresa_id").eq("tenant_id", tenant_id).limit(1).execute()
    if notes.data:
        print(f"Nota Fiscal encontrada no tenant. Empresa ID: {notes.data[0].get('empresa_id')}")
    else:
        print("ALERTA: Nenhuma nota fiscal encontrada para este tenant no banco!")

if __name__ == "__main__":
    test_carlos_join()
