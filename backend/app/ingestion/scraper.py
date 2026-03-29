import requests
from bs4 import BeautifulSoup

def scrape_schemes(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    schemes = []

    for item in soup.select(".scheme-card"):
        schemes.append({
            "name": item.select_one(".title").text,
            "description": item.select_one(".desc").text
        })

    return schemes