import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Government API Key
GOV_API_KEY = os.getenv("GOV_API_KEY", "demo_key")

# Optional: App settings
APP_NAME = "SchemeHouse AI"
DEBUG = True