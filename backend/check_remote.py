import urllib.request
import json

try:
    url = "https://painelcont-production-b6dc.up.railway.app/api/debug-env"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode())
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}")
