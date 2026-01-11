import requests
import json

# Adjust URL based on where the django server is running. usually localhost:8000
url = "https://api.ezrun.in/api/solar/stats"
params = {
    "device_id": "1CSNISHITKUMAWAT",
    "period": "day"
}

try:
    print(f"Fetching from {url} with params {params}...")
    response = requests.get(url, params=params, timeout=5)
    
    if response.status_code == 200:
        data = response.json()
        print("\n--- API RESPONSE SUCCESS ---")
        
        # Check Location
        loc = data.get('location', {})
        print(f"Location Object keys: {loc.keys()}")
        print(f"Location Data: {loc}")
        
        if 'lat' not in loc:
             print("!!! FAILURE: 'lat' key missing in live response. Backend code NOT updated on live server. !!!")
        else:
             print("SUCCESS: 'lat' key present. Backend code likely updated.")
        
        # Check Data Points
        points = data.get('data', [])
        print(f"Data Points Count: {len(points)}")
        if points:
            print(f"Sample Point: {points[0]}")
            print(f"Latest Point: {points[-1]}")
            
        print("----------------------------")
    else:
        print(f"--- API FAILED: {response.status_code} ---")
        print(response.text)

except Exception as e:
    print(f"--- EXCEPTION: {e} ---")
    print("Ensure the Django server is running on port 8000!")
