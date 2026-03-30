import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app_v5.core.supabase_client import SupabaseService

def main():
    service = SupabaseService()
    client = service.get_service_client()
    
    devito_cnpj = "16968599000191"
    
    res_emitidas = client.table("notas_fiscais").select("id", count="exact").eq("emitente_cnpj", devito_cnpj).execute()
    print(f"DE VITO - Emitidas: {res_emitidas.count}")
    
    res_recebidas = client.table("notas_fiscais").select("id", count="exact").eq("destinatario_cnpj", devito_cnpj).execute()
    print(f"DE VITO - Recebidas: {res_recebidas.count}")

if __name__ == "__main__":
    main()
