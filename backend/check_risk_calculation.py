import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_metrics():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    data_limite = "2026-01-01" # Ensuring we capture the test data date

    # 1. Total Notas
    res_total = supabase.table("notas_fiscais").select("id", count="exact").gte("created_at", data_limite).execute()
    total = res_total.count
    
    # 2. Notas Irregulares
    res_error = supabase.table("notas_fiscais").select("id", count="exact").eq("status", "irregular").gte("created_at", data_limite).execute()
    errors = res_error.count

    # 3. Check specific note for the test alert
    note_id = "8f023efd-09d8-4b5d-b00f-465d35e2ab16"
    res_note = supabase.table("notas_fiscais").select("status, numero").eq("id", note_id).execute()
    
    print(f"--- DIAGNOSTIC ---")
    print(f"Total Notes: {total}")
    print(f"Irregular Notes: {errors}")
    if total and total > 0:
        print(f"Risk Score: {int((errors/total)*100)}%")
    else:
        print("Risk Score: 0% (No notes)")
        
    print(f"\nTest Note ({note_id}) Status:")
    if res_note.data:
        print(res_note.data[0])
    else:
        print("Note not found.")

if __name__ == "__main__":
    check_metrics()
