import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Carregar variáveis do backend/.env
load_dotenv("backend/.env")

def main():
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    if not url or not key:
        print("Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY ausentes.")
        return

    client = create_client(url, key)
    
    # 1. Aplicar Migração SQL (UF na tabela empresas)
    print("--- Verificando coluna UF ---")
    try:
        # Tenta um select de teste
        client.table('empresas').select('uf').limit(1).execute()
        print("Coluna UF já existe.")
    except Exception as e:
        print(f"Atenção: Coluna UF parece ausente: {e}")
        print("POR FAVOR: Execute o arquivo 'supabase/migrations/022_add_uf_to_empresas.sql' no seu dashboard Supabase.")
        return

    # 2. Resetar status e Backfill UF
    print("\n--- Resetando status e Corrigindo UF ---")
    client.table('empresas').update({'uf': 'GO'}).eq('cnpj', '16968599000191').execute()
    client.table('empresas').update({'uf': 'GO'}).eq('cnpj', '16.968.599/0001-91').execute()
    
    res_reset = client.table('certificados_a1').update({'status': 'ativo'}).neq('status', 'ativo').execute()
    print(f"Sucesso! {len(res_reset.data)} certificados resetados para 'ativo'.")

    # 3. Mostrar estado final
    print("\n--- Estado Final ---")
    res_final = client.table('certificados_a1').select('empresa_id', 'status').execute()
    for row in res_final.data:
        print(f"Empresa: {row['empresa_id']} -> Status: {row['status']}")

if __name__ == "__main__":
    main()
