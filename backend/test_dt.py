from datetime import datetime, timedelta, timezone

def test_datetime_subtraction():
    aware = datetime.now(timezone.utc)
    naive = datetime.utcnow()
    
    print(f"Aware type: {type(aware)}")
    print(f"Naive type: {type(naive)}")
    
    try:
        diff = aware - naive
        print(f"Subtraction worked: {diff}")
    except TypeError as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_datetime_subtraction()
