import requests
import time

BASE_URL = "http://localhost:8000"

def run_smoke_test():
    print("Running Smoke Tests...")
    endpoints = [
        {"method": "GET", "url": "/health"},
        {"method": "GET", "url": "/api/metrics/all?limit=1"},
        {"method": "GET", "url": "/api/optimize/preview"},
        {"method": "GET", "url": "/api/forecast"},
        {"method": "GET", "url": "/api/rl/stats"}
    ]
    
    success = True
    for ep in endpoints:
        try:
            if ep["method"] == "GET":
                r = requests.get(BASE_URL + ep["url"], timeout=5)
            # Assuming these return 200 or 401 (if missing auth). If 401, that's expected for some, 
            # but backend runs with auth_required=False locally or we can use a mock token.
            print(f"{ep['method']} {ep['url']} -> {r.status_code}")
            if r.status_code not in [200, 401, 403]:
                print(f"FAIL: {ep['url']} returned {r.status_code}")
                success = False
            else:
                print(f"PASS: {ep['url']}")
        except Exception as e:
            print(f"FAIL: {ep['url']} unreachable - {e}")
            success = False

    print(f"Smoke Test {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    exit(0 if run_smoke_test() else 1)
