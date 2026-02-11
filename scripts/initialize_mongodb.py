"""
MongoDB Initialization Script
Creates required collections and indexes on first run
"""
import sys
from db.mongo_client import get_mongo_client, get_db
from utils.logger import get_logger

logger = get_logger(__name__)

def initialize_mongodb():
    """Initialize MongoDB collections and indexes."""
    try:
        client = get_mongo_client()
        client.server_info()  # Verify connection
        db = get_db()
        
        # Define collections and their schemas
        collections_config = {
            "documents": {
                "indexes": [
                    ("filename", {}),
                    ("department", {}),
                    ("service", {}),
                ]
            },
            "chat_history": {
                "indexes": [
                    ("chat_id", {"unique": True}),
                    ("created_at", {"unique": False}),
                    ("updated_at", {"unique": False}),
                ]
            },
            "logs": {
                "indexes": [
                    ("action", {}),
                    ("timestamp", {"unique": False}),
                    ("department", {}),
                ]
            },
            "services": {
                "indexes": [
                    (("department", "service"), {"unique": True}),
                    ("status", {}),
                ]
            },
            "dashboard": {
                "indexes": []
            }
        }
        
        # Create collections and indexes
        for collection_name, config in collections_config.items():
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"✓ Created collection: {collection_name}")
            else:
                logger.info(f"ℹ Collection already exists: {collection_name}")
            
            # Create indexes
            collection = db[collection_name]
            for index_spec in config.get("indexes", []):
                try:
                    if isinstance(index_spec[0], tuple):
                        # Compound index
                        collection.create_index(index_spec[0], **index_spec[1])
                        logger.info(f"  ✓ Created index: {index_spec[0]}")
                    else:
                        # Single field index
                        collection.create_index(index_spec[0], **index_spec[1])
                        logger.info(f"  ✓ Created index: {index_spec[0]}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not create index {index_spec}: {e}")
        
        logger.info(f"✓ MongoDB initialization complete for database: {db.name}")
        return True
        
    except Exception as e:
        logger.error(f"✗ MongoDB initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = initialize_mongodb()
    sys.exit(0 if success else 1)
