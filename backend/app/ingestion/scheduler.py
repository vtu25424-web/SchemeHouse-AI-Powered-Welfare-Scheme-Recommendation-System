from apscheduler.schedulers.background import BackgroundScheduler
from app.ingestion.scraper import scrape_schemes
from app.database.collections import schemes_collection

def update_schemes():
    new_data = scrape_schemes("https://www.myscheme.gov.in/")

    for scheme in new_data:
        schemes_collection.update_one(
            {"name": scheme["name"]},
            {"$set": scheme},
            upsert=True
        )

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_schemes, "interval", hours=24)
    scheduler.start()