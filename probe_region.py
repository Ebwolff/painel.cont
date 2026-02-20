import socket

regions = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "sa-east-1", "eu-central-1", "eu-west-1", "eu-west-2",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ca-central-1"
]

project_ref = "uycsxowdzuuuyahdqspk"
password_encoded = "Eb91412518%21"

for region in regions:
    host = f"aws-0-{region}.pooler.supabase.com"
    # Try a simple TCP connection first
    try:
        with socket.create_connection((host, 6543), timeout=3):
            print(f"Region {region} ({host}) is TCP-UP")
    except:
        continue
    
    # If TCP is up, the region exists. 
    # To truly verify if the tenant is there, we need to try a real Postgres handshake.
    # But since I don't have psycopg2, I'll just report TCP-UP.
    # Wait, the CLI already told me sa-east-1 and us-east-1 were TCP-UP but tenant-less.
