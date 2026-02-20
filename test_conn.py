import socket
import ssl

def check_port(host, port):
    try:
        sock = socket.create_connection((host, port), timeout=2)
        sock.close()
        return True
    except:
        return False

regions = [
    "sa-east-1", "us-east-1", "us-west-1", "eu-west-1", "eu-central-1", 
    "ap-southeast-1", "ap-northeast-1", "us-east-2"
]

project_ref = "uycsxowdzuuuyahdqspk"

print(f"Testing regions for project {project_ref}...")

for region in regions:
    host = f"aws-0-{region}.pooler.supabase.com"
    if check_port(host, 6543):
        print(f"[OK] {region} ({host}) is reachable on 6543")
    else:
        # print(f"[FAIL] {region}")
        pass

print("Testing direct host...")
host_direct = f"db.{project_ref}.supabase.co"
if check_port(host_direct, 5432):
    print(f"[OK] Direct host {host_direct} is reachable on 5432")
else:
    print(f"[FAIL] Direct host {host_direct} is unreachable")
