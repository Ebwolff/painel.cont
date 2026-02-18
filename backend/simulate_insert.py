import os
import uuid
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def simulate_backend_insert():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"URL: {url}")
    supabase = create_client(url, service_key)

    # 1. Pegar um tenant e empresa reais para evitar erro de FK
    try:
        tenant = supabase.table("tenants").select("id").limit(1).execute()
        if not tenant.data:
            print("❌ Erro: Nenhum tenant encontrado.")
            return
        tenant_id = tenant.data[0]['id']
        
        empresa = supabase.table("empresas").select("id").eq("tenant_id", tenant_id).limit(1).execute()
        empresa_id = empresa.data[0]['id'] if empresa.data else None
        
        print(f"Tenant ID: {tenant_id}")
        print(f"Empresa ID: {empresa_id}")

        # 2. Dados fake de nota
        nota_payload = {
            "tenant_id": tenant_id,
            "empresa_id": empresa_id,
            "chave_acesso": "TESTE" + str(uuid.uuid4())[:20],
            "numero": "123",
            "serie": "1",
            "data_emissao": "2024-02-17T12:00:00Z",
            "emitente_cnpj": "00.000.000/0001-91",
            "destinatario_cnpj": "11.111.111/0001-91",
            "valor_total": 1000.0,
            "valor_cbs": 9.0,
            "valor_ibs": 1.0,
            "cbs_correto": True,
            "ibs_correto": True,
            "status": "conforme"
        }

        print("Tentando inserir nota...")
        res = supabase.table("notas_fiscais").insert(nota_payload).execute()
        print(f"✅ Inserção nota: OK (ID: {res.data[0]['id']})")
        
        nota_id = res.data[0]['id']

        # 3. Alerta fake
        alerta_payload = {
            "tenant_id": tenant_id,
            "nota_fiscal_id": nota_id,
            "tipo": "teste",
            "severidade": "baixa",
            "mensagem": "Alerta de teste técnico",
            "valor_esperado": 0,
            "valor_encontrado": 0,
            "diferenca": 0
        }
        
        print("Tentando inserir alerta...")
        res_alerta = supabase.table("alertas_conformidade").insert(alerta_payload).execute()
        print(f"✅ Inserção alerta: OK")

    except Exception as e:
        print(f"🚨 FALHA NA SIMULAÇÃO: {str(e)}")

if __name__ == "__main__":
    simulate_backend_insert()
