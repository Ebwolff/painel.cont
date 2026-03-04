import os
from supabase import create_client
from dotenv import load_dotenv

def main():
    # 1. Configurar cliente Supabase (usando service role para ignorar RLS se necessário)
    load_dotenv('backend/.env')
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Erro: SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não encontrados no .env")
        return

    client = create_client(url, key)
    empresa_id = '995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8'
    cnpj = '16968599000191'

    print(f"--- Resetando Empresa {empresa_id} ---")
    
    # 1. Garantir que a UF está correta
    client.table('empresas').update({'uf': 'GO'}).eq('id', empresa_id).execute()
    print("UF atualizada para 'GO'.")

    # 2. Resetar status do certificado para 'ativo' (independente do status atual)
    # Removemos filtros restritivos para garantir o reset
    res = client.table('certificados_a1').update({'status': 'ativo'}).eq('empresa_id', empresa_id).execute()
    
    if res.data:
        print(f"Sucesso! Certificado resetado para 'ativo'.")
    else:
        print("Aviso: Nenhum certificado encontrado para esta empresa ou falha no update.")

    # 3. Mostrar estado final
    final = client.table('certificados_a1').select('status').eq('empresa_id', empresa_id).maybe_single().execute()
    if final.data:
        print(f"Estado Final no Banco: {final.data['status']}")

if __name__ == "__main__":
    main()
