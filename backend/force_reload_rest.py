import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def force_reload():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not service_key:
        print("Erro: Credenciais não encontradas.")
        return

    # O Supabase permite recarregar o esquema enviando um NOTIFY via SQL.
    # Como não temos client SQL raw aqui, vamos usar a API REST para tentar "provocar" um erro que force o reload
    # ou tentar usar o endpoint de saúde se disponível.
    
    # Outra forma é usar o PostgREST direto se soubermos o endpoint, mas o NOTIFY SQL é o ideal.
    # Vamos tentar via HTTP se o Supabase expõe algo, mas geralmente é só via SQL.
    
    print(f"Tentando forçar visibilidade em: {url}")
    
    # Vamos tentar um POST que sabemos que falharia se a tabela não existisse, 
    # mas o objetivo é que o PostgREST perceba a mudança.
    
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    }
    
    # Tenta dar um GET na tabela. Se o PostgREST recarregou, deve funcionar.
    try:
        response = httpx.get(f"{url}/rest/v1/notas_fiscais?select=id&limit=1", headers=headers)
        if response.status_code == 200:
            print("✅ Sucesso! A tabela agora está visível para a API REST.")
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")
    except Exception as e:
        print(f"🚨 Erro na requisição: {str(e)}")

if __name__ == "__main__":
    force_reload()
