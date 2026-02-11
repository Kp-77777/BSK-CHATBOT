"""
Initialization and startup checks for BSK Assistant
Ensures all required services are available and databases are initialized
"""
import os
import sys
import time
from typing import Dict, Tuple
import requests
from dotenv import load_dotenv
from utils.logger import get_logger
from config.settings import MODEL_CONFIG, VECTOR_STORE_CONFIG

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bsk_assistant")

logger = get_logger(__name__)


class ServiceInitializer:
    """Handles initialization and health checks for all services."""
    
    @staticmethod
    def check_ollama_service() -> bool:
        """Check if Ollama service is running and accessible."""
        try:
            ollama_base_url = MODEL_CONFIG.get("ollama_base_url", "http://localhost:11434")
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                logger.info(f"✓ Ollama service is running at {ollama_base_url}")
                return True
            else:
                logger.error(f"✗ Ollama service returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error(
                f"✗ Cannot connect to Ollama service at {MODEL_CONFIG.get('ollama_base_url', 'http://localhost:11434')}. "
                "Make sure Ollama is running."
            )
            return False
        except Exception as e:
            logger.error(f"✗ Error checking Ollama service: {e}")
            return False
    
    @staticmethod
    def check_chat_model_available() -> bool:
        """Check if the chat model is available in Ollama."""
        try:
            ollama_base_url = MODEL_CONFIG.get("ollama_base_url", "http://localhost:11434")
            chat_model = MODEL_CONFIG.get("chat_model", "llama3.1:latest")
            
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if any(chat_model in name for name in model_names):
                    logger.info(f"✓ Chat model '{chat_model}' is available")
                    return True
                else:
                    logger.warning(
                        f"✗ Chat model '{chat_model}' not found in Ollama. "
                        f"Available models: {model_names}. "
                        f"Pull the model with: ollama pull {chat_model}"
                    )
                    return False
            return False
        except Exception as e:
            logger.error(f"✗ Error checking chat model: {e}")
            return False
    
    @staticmethod
    def check_embedding_model_available() -> bool:
        """Check if the embedding model is available in Ollama."""
        try:
            ollama_base_url = MODEL_CONFIG.get("ollama_base_url", "http://localhost:11434")
            embedding_model = MODEL_CONFIG.get("embedding_model", "mxbai-embed-large:latest")
            
            response = requests.get(f"{ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if any(embedding_model in name for name in model_names):
                    logger.info(f"✓ Embedding model '{embedding_model}' is available")
                    return True
                else:
                    logger.warning(
                        f"✗ Embedding model '{embedding_model}' not found in Ollama. "
                        f"Pull the model with: ollama pull {embedding_model}"
                    )
                    return False
            return False
        except Exception as e:
            logger.error(f"✗ Error checking embedding model: {e}")
            return False
    
    @staticmethod
    def check_mongodb_connection() -> bool:
        """Check if MongoDB is accessible and create collections if needed."""
        try:
            from db.mongo_client import get_mongo_client, get_db

            client = get_mongo_client()
            # Attempt to get server info to verify connection
            client.server_info()

            logger.info(f"??? MongoDB connection successful ({MONGO_URI})")

            # Auto-create collections if they don't exist
            db = get_db()
            collections_to_create = ["chat_history", "documents", "logs", "services"]

            for collection_name in collections_to_create:
                if collection_name not in db.list_collection_names():
                    db.create_collection(collection_name)
                    logger.info(f"  ??? Created MongoDB collection: {collection_name}")
                else:
                    logger.debug(f"  ??? Collection already exists: {collection_name}")

            # Create indexes and seed services explicitly
            try:
                from core.db_manager import initialize_collections
                initialize_collections()
            except Exception as e:
                logger.error(f"??? Error initializing MongoDB collections/indexes: {e}")

            return True
        except Exception as e:
            logger.error(f"??? MongoDB connection failed: {e}")
            logger.error(f"   Make sure MongoDB is running at {MONGO_URI}")
            return False

    @staticmethod
    def check_chroma_vectorstore() -> bool:
        """Check if Chroma vector store is initialized and accessible."""
        try:
            from core.vector_store import vector_store_manager
            
            if vector_store_manager.is_available():
                logger.info(f"✓ Chroma vector store is available (persist dir: {vector_store_manager.persist_directory})")
                return True
            else:
                logger.error("✗ Chroma vector store is not available")
                return False
        except Exception as e:
            logger.error(f"✗ Error checking Chroma vector store: {e}")
            return False
    
    @staticmethod
    def run_all_checks(exit_on_failure: bool = False) -> Tuple[Dict[str, bool], bool]:
        """
        Run all initialization checks.
        
        Returns:
            Tuple of (results_dict, all_passed)
        """
        logger.info("=" * 60)
        logger.info("Starting BSK Assistant Initialization Checks")
        logger.info("=" * 60)
        
        results = {
            "ollama_service": ServiceInitializer.check_ollama_service(),
            "chat_model": ServiceInitializer.check_chat_model_available(),
            "embedding_model": ServiceInitializer.check_embedding_model_available(),
            "mongodb": ServiceInitializer.check_mongodb_connection(),
            "chroma_vectorstore": ServiceInitializer.check_chroma_vectorstore(),
        }
        
        logger.info("=" * 60)
        logger.info("Initialization Check Summary:")
        logger.info("=" * 60)
        for service, status in results.items():
            status_str = "✓ PASS" if status else "✗ FAIL"
            logger.info(f"{status_str}: {service}")
        logger.info("=" * 60)
        
        # Critical services that must pass
        critical_services = ["ollama_service", "mongodb"]
        all_critical_passed = all(results[service] for service in critical_services)
        
        if exit_on_failure and not all_critical_passed:
            logger.error("Critical services failed. Exiting...")
            sys.exit(1)
        
        return results, all_critical_passed


def initialize_app():
    """Initialize the application on startup."""
    logger.info("Initializing BSK Assistant Application...")
    
    # Run startup checks
    results, critical_passed = ServiceInitializer.run_all_checks(exit_on_failure=False)
    
    if critical_passed:
        logger.info("✓ All critical services initialized successfully!")
    else:
        logger.warning("⚠ Some services are not available. App may have limited functionality.")
    
    return results
