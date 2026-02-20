import asyncio
import os
import sys

# Adiciona o diretório atual ao path para os imports funcionarem
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app_v5.services.sefaz_sync import SefazSyncService
from app_v5.core.supabase_client import SupabaseService

async def main():
    service = SefazSyncService()
    supabase = SupabaseService()
    
    # Vamos tentar pegar uma empresa e tenant reais do banco para o teste ser fiel
    try:
        client = supabase.get_service_client()
        res = client.table("empresas").select("id, tenant_id").limit(1).execute()
        
        if not res.data:
            print("Nenhuma empresa encontrada para teste. Crie uma empresa primeiro.")
            return
            
        empresa_id = res.data[0]['id']
        tenant_id = res.data[0]['tenant_id']
        
        print(f"--- Iniciando Teste de Sincronização Inteligente ---")
        print(f"Empresa: {empresa_id}")
        print(f"Tenant: {tenant_id}")
        print("-" * 50)
        
        result = await service.sync_company_documents(empresa_id, tenant_id)
        
        print(f"Resultado do Sync: {result}")
        
        if result['status'] == 'success':
            nota_id = result['nota_id']
            
            # Verificar se os itens foram criados
            itens_res = client.table("nfe_items").select("*").eq("nota_fiscal_id", nota_id).execute()
            print(f"Itens criados no banco: {len(itens_res.data)}")
            for item in itens_res.data:
                print(f"  - Item {item['n_item']}: NCM {item['ncm']} | CBS OK: {item['cbs_correto']}")
            
            # Verificar se os alertas gerenciáveis foram criados
            alertas_res = client.table("alerts_management").select("*").eq("nfe_id", nota_id).execute()
            print(f"Alertas de gestão criados: {len(alertas_res.data)}")
            
        print("-" * 50)
        print("Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
