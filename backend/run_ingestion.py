from app.ingestion.scraper import scrape_schemes
from app.ingestion.api_fetcher import fetch_schemes_from_api
from app.ingestion.parser import clean_scheme
from app.database.collections import schemes_collection

def run_ingestion():
    print("🚀 Starting ingestion...")

    all_data = []

    # 1. Try API
    api_data = fetch_schemes_from_api()
    all_data.extend(api_data)

    # 2. Always run scraper ALSO (as you requested)
    scraped_data = scrape_schemes("https://www.myscheme.gov.in")
    all_data.extend(scraped_data)

    if not all_data:
        print("❌ No data fetched from API or scraper")
        return

    # 3. Store in DB (remove duplicates)
    unique_names = set()

    count = 0

    for item in all_data:
        clean_data = clean_scheme(item)

        if not clean_data.get("name"):
            continue

        if clean_data["name"] in unique_names:
            continue

        unique_names.add(clean_data["name"])

        schemes_collection.update_one(
            {"name": clean_data["name"]},
            {"$set": clean_data},
            upsert=True
        )

        count += 1

    print(f"✅ Total {count} schemes stored in DB")


if __name__ == "__main__":
    run_ingestion()