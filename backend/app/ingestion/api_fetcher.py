import requests
from app.utils.config import GOV_API_KEY

def fetch_schemes_from_api():
    url = "https://www.myscheme.gov.in/search"  # ⚠️ Replace with real API

    headers = {
        "Authorization": f"Bearer {GOV_API_KEY}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        # Check if response is OK
        if response.status_code != 200:
            print("❌ API failed with status:", response.status_code)
            return []

        # Check if response is JSON
        if "application/json" not in response.headers.get("Content-Type", ""):
            print("❌ API did not return JSON")
            return []

        data = response.json()

        print(f"✅ API fetched {len(data)} schemes")
        return data

    except Exception as e:
        print("❌ API Error:", str(e))
        return []