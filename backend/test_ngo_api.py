import requests
import json

BASE_URL = "http://localhost:8000/api"

# We need a valid token. Since I can't easily get one, 
# I'll just check if the backend is reachable and what the error is.
try:
    # First, try to hit without auth to see if route exists
    r = requests.get(f"{BASE_URL}/ngo/stats")
    print(f"Stats status: {r.status_code}")
    print(f"Stats body: {r.text}")
except Exception as e:
    print(f"Error: {e}")

