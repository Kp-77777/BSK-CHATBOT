"""
Embedding models configuration using Ollama Nomic for local deployment
"""
from langchain_community.embeddings import OllamaEmbeddings
from config.settings import MODEL_CONFIG, EMBEDDING_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

def get_embeddings():
    """Get embedding model instance using Ollama Nomic."""
    try:
        # --- Ollama Nomic embeddings pipeline (local, for Pinecone, RAG, etc.) ---
        embedding_model = EMBEDDING_MODEL
        ollama_base_url = MODEL_CONFIG.get("ollama_base_url", "http://localhost:11434")
        
        embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=ollama_base_url
        )
        logger.info(f"Ollama  embeddings initialized successfully ({embedding_model}) from {ollama_base_url}")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize Ollama Nomic embeddings: {e}")
        raise