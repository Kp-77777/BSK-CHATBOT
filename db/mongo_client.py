import os
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Use MONGODB_URI with local default, fallback to MONGO_URI if set
MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bsk_assistant")

_mongo_client: MongoClient | None = None

def get_mongo_client() -> MongoClient:
    """Get a shared MongoClient with sane defaults for local/remote MongoDB."""
    global _mongo_client
    if _mongo_client is None:
        if not MONGO_URI:
            raise ValueError("MONGODB_URI/MONGO_URI not found. Check your .env file.")
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _mongo_client

def get_db():
    """Get the configured MongoDB database."""
    client = get_mongo_client()
    return client[MONGO_DB_NAME]

db = get_db()

services_collection = db["services"]
documents_collection = db["documents"]
logs_collection = db["logs"]
