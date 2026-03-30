from pymongo import MongoClient
from app.utils.config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["schemehouse"]

def get_db():
    return db