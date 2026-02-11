"""
Ollama Service Health Check
Verifies that Ollama is running and models are available
"""
import os
import sys
import requests
from dotenv import load_dotenv
from utils.logger import get_logger
from config.settings import MODEL_CONFIG

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

def check_ollama_health():
    """Check Ollama service health and model availability."""
    try:
        ollama_url = MODEL_CONFIG.get("ollama_base_url", "http://localhost:11434")
        embedding_model = MODEL_CONFIG.get("embedding_model", "mxbai-embed-large:latest")
        chat_model = MODEL_CONFIG.get("chat_model", "llama3.1:latest")
        
        logger.info(f"Checking Ollama Service at {ollama_url}...")
        
        # Check service availability
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        
        if response.status_code != 200:
            logger.error(f"✗ Ollama service not responding (status {response.status_code})")
            return False
        
        logger.info("✓ Ollama service is running")
        
        # Check available models
        models_resp = response.json()
        available_models = [m.get("name", "") for m in models_resp.get("models", [])]
        
        logger.info(f"Available models: {available_models}")
        
        # Check embedding model
        embedding_available = any(embedding_model in m for m in available_models)
        if embedding_available:
            logger.info(f"✓ Embedding model available: {embedding_model}")
        else:
            logger.warning(f"⚠ Embedding model not found: {embedding_model}")
            logger.info(f"  Pull with: ollama pull {embedding_model}")
        
        # Check chat model
        chat_available = any(chat_model in m for m in available_models)
        if chat_available:
            logger.info(f"✓ Chat model available: {chat_model}")
        else:
            logger.warning(f"⚠ Chat model not found: {chat_model}")
            logger.info(f"  Pull with: ollama pull {chat_model}")
        
        return embedding_available and chat_available
        
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ Cannot connect to Ollama at {MODEL_CONFIG.get('ollama_base_url', 'http://localhost:11434')}")
        logger.error("  Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        logger.error(f"✗ Ollama health check error: {e}")
        return False

if __name__ == "__main__":
    success = check_ollama_health()
    sys.exit(0 if success else 1)
