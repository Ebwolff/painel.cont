import sys
import os
from datetime import datetime, timezone, timedelta

# Add current dir to sys.path
sys.path.append(os.getcwd())

from app_v5.routers.certificates import _read_cert_expiry

def test_expiry_fallback():
    print("Testing _read_cert_expiry fallback (dummy data)...")
    # This should trigger the Exception and return the fallback (now timezone-aware)
    expiry = _read_cert_expiry(b"invalid-pfx", "wrong-password")
    print(f"Expiry: {expiry} (tzinfo: {expiry.tzinfo})")
    
    now = datetime.now(timezone.utc)
    print(f"Now: {now} (tzinfo: {now.tzinfo})")
    
    # This was the failing line (subtraction)
    try:
        diff = expiry - now
        print(f"Subtraction worked! Difference: {diff}")
        assert isinstance(diff, timedelta)
        print("Verification SUCCESS: Timezone awareness conflict resolved.")
    except TypeError as e:
        print(f"Verification FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_expiry_fallback()
