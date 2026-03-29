from app.database.collections import schemes_collection

def init_db():
    if schemes_collection.count_documents({}) == 0:
        print("DB initialized: No schemes found")