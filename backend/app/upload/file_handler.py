from app.database.collections import schemes_collection

def save_uploaded_schemes(data):
    for scheme in data:
        schemes_collection.insert_one(scheme)