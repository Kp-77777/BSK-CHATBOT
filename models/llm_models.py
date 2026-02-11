"""
Language model configurations - Using Ollama for local deployment
"""
from langchain_community.chat_models.ollama import ChatOllama
from config.settings import MODEL_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

def get_chat_model():
    """Get main chat model instance using Ollama Llama 3.1."""
    try:
        # --- Ollama Llama 3.1 integration ---
        chat_model = MODEL_CONFIG.get("chat_model", "llama3.1:latest")
        ollama_base_url = MODEL_CONFIG.get("ollama_base_url", "http://localhost:11434")
        streaming = MODEL_CONFIG.get("streaming", False)
        
        model = ChatOllama(
            model=chat_model,
            base_url=ollama_base_url,
            temperature=MODEL_CONFIG.get("temperature", 0.2),
            num_ctx=MODEL_CONFIG.get("n_ctx", 16384),
            num_predict=MODEL_CONFIG.get("max_output_tokens", 8192),
            streaming=streaming
        )
        logger.info(f"Ollama Llama 3.1 model initialized successfully from {ollama_base_url}")
        logger.info(f"  Model: {chat_model}")
        logger.info(f"  Temperature: {MODEL_CONFIG.get('temperature', 0.2)}")
        logger.info(f"  Streaming: {streaming}")
        logger.info(f"  Context size: {MODEL_CONFIG.get('n_ctx', 16384)}")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Ollama Llama 3.1 model: {e}")
        logger.error("Make sure Ollama is running and the model is pulled:")
        logger.error(f"  ollama pull {MODEL_CONFIG.get('chat_model', 'llama3.1:latest')}")
        raise

