import requests
import json

url = "https://api.ezrun.in/api/solar/stats"
params = {"device_id": "1CSNISHITKUMAWAT", "period": "day"}

try:
    print(f"Fetching {url}...")
    r = requests.get(url, params=params, timeout=10)
    data = r.json()
    
    print("\nXXX START LIVE RESPONSE XXX")
    print(json.dumps(data.get('location'), indent=4))
    print("XXX END LIVE RESPONSE XXX")
    
except Exception as e:
    print(e)
