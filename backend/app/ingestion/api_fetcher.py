import requests
from app.config import GOV_API_KEY

def fetch_schemes_from_api():
    url = "https://www.myscheme.gov.in/"
    
    headers = {
        "Authorization": f"Bearer {GOV_API_KEY}"
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    
    return []