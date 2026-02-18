import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def update_risk():
    url = os.environ.get("SUPABASE_URL")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, service_key)

    note_id = "8f023efd-09d8-4b5d-b00f-465d35e2ab16"
    
    print(f"Updating note {note_id} to status 'irregular'...")
    
    try:
        res = supabase.table("notas_fiscais").update({"status": "irregular"}).eq("id", note_id).execute()
        if res.data:
            print("Success! Updated note status:", res.data[0]['status'])
        else:
            print("No data returned. Check if ID exists.")
            
    except Exception as e:
        print(f"Error updating note: {e}")

if __name__ == "__main__":
    update_risk()
