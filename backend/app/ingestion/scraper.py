import requests
from bs4 import BeautifulSoup

# ❌ words to ignore
IGNORE_KEYWORDS = [
    "screen reader",
    "accessibility",
    "faq",
    "terms",
    "privacy",
    "login",
    "register",
    "skip",
    "content"
]

def is_valid_scheme(name):
    name = name.lower()

    # Filter junk links
    for word in IGNORE_KEYWORDS:
        if word in name:
            return False

    # Only meaningful names
    if len(name) < 15:
        return False

    return True


def scrape_schemes(url):
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print("❌ Scraper failed:", response.status_code)
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        schemes = []
        seen = set()

        # Try extracting meaningful text blocks
        tags = soup.find_all(["h2", "h3", "p", "a"])

        for tag in tags:
            text = tag.get_text(strip=True)

            if not text:
                continue

            if not is_valid_scheme(text):
                continue

            if text in seen:
                continue

            seen.add(text)

            schemes.append({
                "name": text,
                "description": "Extracted from myscheme.gov.in"
            })

            # limit results
            if len(schemes) >= 20:
                break

        print(f"✅ Scraper fetched {len(schemes)} schemes")
        return schemes

    except Exception as e:
        print("❌ Scraper Error:", str(e))
        return []