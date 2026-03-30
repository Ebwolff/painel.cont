"""
Check: quantas notas têm emitente_cnpj NULL ou vazio? E quantas 'is_resumo'?
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app_v5.core.supabase_client import SupabaseService

def main():
    service = SupabaseService()
    client = service.get_service_client()
    devito_id = "995ef420-3ea5-44fe-b3eb-3ff15b3f3fd8"
    
    # Notas sem emitente_cnpj
    null_emit = client.table("notas_fiscais").select("id", count="exact").eq("empresa_id", devito_id).is_("emitente_cnpj", "null").execute()
    print(f"Notas com emitente_cnpj NULL: {null_emit.count}")
    
    # Notas com is_resumo = true
    resumos = client.table("notas_fiscais").select("id", count="exact").eq("empresa_id", devito_id).eq("is_resumo", True).execute()
    print(f"Notas is_resumo=true: {resumos.count}")
    
    # Notas com manifestado = false
    nao_manif = client.table("notas_fiscais").select("id", count="exact").eq("empresa_id", devito_id).eq("manifestado", False).execute()
    print(f"Notas manifestado=false: {nao_manif.count}")
    
    # Notas onde emitente_cnpj = CNPJ da DE VITO (seria emitida)
    emitidas_real = client.table("notas_fiscais").select("id, numero, emitente_cnpj, emitente_nome", count="exact").eq("empresa_id", devito_id).eq("emitente_cnpj", "16968599000191").execute()
    print(f"Notas realmente emitidas pela DE VITO: {emitidas_real.count}")
    
    # Amostra de 5 notas que não são nem emitidas nem recebidas pela DE VITO
    sample = client.table("notas_fiscais").select("id, numero, emitente_cnpj, emitente_nome, destinatario_cnpj, destinatario_nome, is_resumo, status").eq("empresa_id", devito_id).neq("emitente_cnpj", "16968599000191").neq("destinatario_cnpj", "16968599000191").limit(5).execute()
    print(f"\nAmostra de notas 'orfãs' (nem emit nem dest = DE VITO):")
    for n in (sample.data or []):
        print(f"  Numero: {n.get('numero')} | Emit: {n.get('emitente_cnpj')} ({n.get('emitente_nome')}) | Dest: {n.get('destinatario_cnpj')} ({n.get('destinatario_nome')}) | Resumo: {n.get('is_resumo')} | Status: {n.get('status')}")

if __name__ == "__main__":
    main()
