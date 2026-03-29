from app.ingestion.scraper import scrape_schemes
from app.ingestion.api_fetcher import fetch_schemes_from_api
from app.ingestion.parser import clean_scheme
from app.database.collections import schemes_collection

def run_scraper():
    print("Running scraper...")
    data = scrape_schemes("https://www.myscheme.gov.in/")

    for item in data:
        clean_data = clean_scheme(item)

        schemes_collection.update_one(
            {"name": clean_data["name"]},
            {"$set": clean_data},
            upsert=True
        )

    print(f"{len(data)} schemes stored from scraping")


def run_api_fetch():
    print("Fetching from API...")
    data = fetch_schemes_from_api()

    for item in data:
        clean_data = clean_scheme(item)

        schemes_collection.update_one(
            {"name": clean_data["name"]},
            {"$set": clean_data},
            upsert=True
        )

    print(f"{len(data)} schemes stored from API")


if __name__ == "__main__":
    run_scraper()
    run_api_fetch()