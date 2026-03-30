import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app_v5.core.supabase_client import SupabaseService

def main():
    service = SupabaseService()
    client = service.get_service_client()
    
    notas = client.table("notas_fiscais").select("id, numero, emitente_cnpj, destinatario_cnpj, direcao, empresa_id").limit(20).order('created_at', desc=True).execute()
    print("\n=== NOTAS FISCAIS (CNPJs) ===")
    for n in (notas.data or []):
        print(f"Nota {n.get('numero')}: Emit={n.get('emitente_cnpj')} Dest={n.get('destinatario_cnpj')} Direcao={n.get('direcao')} Empresa={n.get('empresa_id')}")

if __name__ == "__main__":
    main()
