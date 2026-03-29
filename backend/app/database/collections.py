from app.database.mongo_client import get_db

db = get_db()

users_collection = db["users"]
schemes_collection = db["schemes"]
notifications_collection = db["notifications"]