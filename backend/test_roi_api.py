import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# We need a valid token. Since I can't easily get one from here without login, 
# I will simulate the logic or use the service role to call the functions directly if possible,
# or better, just simulate the backend logic in a script.

from app.routers.roi import get_strategic_intel, get_roi_summary

# Mock user object for Depends(get_current_user)
mock_user = {
    'id': '40ce0ec5-4326-4f36-83f8-bbd26897e1eb', # taless
    'email': 'contagro@test.com'
}

def test_api():
    print("--- Testing ROI API Logic ---")
    
    intel = get_strategic_intel(empresa_id=None, user=mock_user)
    print("\nStrategic Intel Response:")
    print(intel)
    
    summary = get_roi_summary(empresa_id=None, user=mock_user)
    print("\nROI Summary Response:")
    print(summary)

if __name__ == "__main__":
    # Ensure PYTHONPATH includes current dir
    import sys
    sys.path.append(os.getcwd())
    test_api()
