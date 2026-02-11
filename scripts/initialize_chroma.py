"""
Chroma Vector Store Initialization Script
Ensures Chroma collection exists and is ready for use
"""
import os
import sys
from dotenv import load_dotenv
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

def initialize_chroma():
    """Initialize Chroma vector store."""
    try:
        from core.vector_store import vector_store_manager
        
        logger.info("Initializing Chroma Vector Store...")
        
        persist_dir = vector_store_manager.persist_directory
        collection_name = vector_store_manager.collection_name
        
        if vector_store_manager.is_available():
            logger.info(f"✓ Chroma initialized successfully")
            logger.info(f"  Persist directory: {persist_dir}")
            logger.info(f"  Collection name: {collection_name}")
            
            # Get stats
            stats = vector_store_manager.get_stats()
            logger.info(f"  Total documents: {stats.get('total_documents', 0)}")
            
            return True
        else:
            logger.error("✗ Failed to initialize Chroma")
            return False
            
    except Exception as e:
        logger.error(f"✗ Chroma initialization error: {e}")
        return False

if __name__ == "__main__":
    success = initialize_chroma()
    sys.exit(0 if success else 1)
