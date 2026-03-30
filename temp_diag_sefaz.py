"""
Diagnóstico: verifica o estado do certificado e do último sync para todas as empresas.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app_v5.core.supabase_client import SupabaseService

def main():
    service = SupabaseService()
    client = service.get_service_client()
    
    # 1. Verificar certificados
    certs = client.table("certificados_a1").select("empresa_id, status, ultimo_sync, ultimo_nsu, ambiente, vencimento").execute()
    print("=" * 70)
    print("CERTIFICADOS A1 CADASTRADOS")
    print("=" * 70)
    for c in (certs.data or []):
        # Buscar nome da empresa
        emp = client.table("empresas").select("razao_social, cnpj").eq("id", c["empresa_id"]).maybe_single().execute()
        nome = emp.data["razao_social"] if emp and emp.data else "???"
        cnpj = emp.data["cnpj"] if emp and emp.data else "???"
        print(f"  Empresa: {nome} (CNPJ: {cnpj})")
        print(f"    Status: {c.get('status')}")
        print(f"    Último Sync: {c.get('ultimo_sync')}")
        print(f"    Último NSU: {c.get('ultimo_nsu')}")
        print(f"    Ambiente: {c.get('ambiente')}")
        print(f"    Vencimento: {c.get('vencimento')}")
        print()
    
    # 2. Verificar últimos sync_jobs
    jobs = client.table("sync_jobs").select("empresa_id, status, started_at, finished_at, notas_processadas, notas_manifestadas, notas_completas, error_message, triggered_by").order("created_at", desc=True).limit(10).execute()
    print("=" * 70)
    print("ÚLTIMOS 10 SYNC JOBS")
    print("=" * 70)
    for j in (jobs.data or []):
        emp = client.table("empresas").select("razao_social").eq("id", j["empresa_id"]).maybe_single().execute()
        nome = emp.data["razao_social"] if emp and emp.data else "???"
        print(f"  {nome} | Status: {j['status']} | Trigger: {j.get('triggered_by')} | Processadas: {j.get('notas_processadas')} | Manifestadas: {j.get('notas_manifestadas')} | Completas: {j.get('notas_completas')}")
        if j.get("error_message"):
            print(f"    ERRO: {j['error_message'][:100]}")
        print()

    # 3. Contar notas por direção
    print("=" * 70)
    print("NOTAS POR EMPRESA E DIREÇÃO")
    print("=" * 70)
    empresas = client.table("empresas").select("id, razao_social, cnpj").execute()
    for e in (empresas.data or []):
        cnpj = e.get("cnpj")
        if not cnpj:
            continue
        emitidas = client.table("notas_fiscais").select("id", count="exact").eq("emitente_cnpj", cnpj).execute()
        recebidas = client.table("notas_fiscais").select("id", count="exact").eq("destinatario_cnpj", cnpj).execute()
        total = client.table("notas_fiscais").select("id", count="exact").eq("empresa_id", e["id"]).execute()
        print(f"  {e['razao_social']} (CNPJ: {cnpj})")
        print(f"    Total no banco: {total.count}")
        print(f"    Emitidas (emitente_cnpj = {cnpj}): {emitidas.count}")
        print(f"    Recebidas (destinatario_cnpj = {cnpj}): {recebidas.count}")
        print()

if __name__ == "__main__":
    main()
