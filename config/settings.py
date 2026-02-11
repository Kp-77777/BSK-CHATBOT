"""
Configuration settings for BSK Assistant - Docker Compatible
All model parameters are fixed here. Only URLs and API keys come from .env
"""
import os
from dotenv import load_dotenv

# Load environment variables (.env file should only contain URLs and API keys)
load_dotenv()

# Page Configuration
PAGE_CONFIG = {
    "page_title": "BSK Assistant",
    "page_icon": "🏛️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# ============================================================================
# MODEL CONFIGURATION - Fixed Parameters
# ============================================================================
EMBEDDING_MODEL = "mxbai-embed-large:latest"

MODEL_CONFIG = {
    # Embedding model for Ollama Nomic
    "embedding_model": EMBEDDING_MODEL,
    "embedding_dim": 1024,
    
    # Llama 3.1 local model (via Ollama)
    "chat_model": "llama3.1:latest",
    
    # Ollama Base URL (from .env)
    "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    
    # LLM Parameters - Fixed
    "temperature": 0.2,
    "streaming": False,
    "max_output_tokens": 8192,
    "n_ctx": 16384,
    "n_gpu_layers": 20
}

# ============================================================================
# VECTOR STORE CONFIGURATION - Embedded Chroma (Local)
# ============================================================================
VECTOR_STORE_CONFIG = {
    "persist_directory": os.getenv("CHROMA_PERSIST_DIRECTORY", "./db/chroma"),
    "collection_name": "bsk_documents",
    "search_type": "similarity",
    "k": 6,
    "fetch_k": 6,
    "lambda_mult": 0.8
}

# ============================================================================
# DATABASE CONFIGURATION - MongoDB (Local Default)
# ============================================================================
DATABASE_CONFIG = {
    "mongo_uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
    "mongo_db_name": os.getenv("MONGO_DB_NAME", "bsk_assistant")
}
# ============================================================================
# MEMORY CONFIGURATION - Fixed Parameters
# ============================================================================
MEMORY_CONFIG = {
    "window_size": 6,
    "return_messages": True,
}

# ============================================================================
# FILE PATHS - Fixed
# ============================================================================
LOG_FILE = "logs/rag_chatbot.log"






SYSTEM_PROMPT ='''
You are a conversational assistant designed exclusively for Bangla Sahayata Kendra (BSK) operators.

ROLE:
- You help BSK operators by providing accurate information about BSK services using ONLY the provided knowledge base context.

SOURCE OF TRUTH:
- The provided context is your only source of information.
- Do NOT use outside knowledge.
- Do NOT assume or generate information that is not present in the context.

STRICT RULE:
- If the context does not contain enough information to answer the query, respond EXACTLY with:
"This information is not available in the official BSK knowledge base. you can ask me any other question related to BSK services."

ANSWERING INSTRUCTIONS:
- Answer only from the provided context.And be complete about the informations.
- Focus only on information relevant to the user’s query.
- Provide clear and simple explanations for eligibility, required documents, application steps, and processing time ONLY if present in context.
- If multiple context sections are provided, combine only the relevant information.
- if the source of context mathches the query service then its a valid service.

STYLE:
- Respond only in English.
- Be friendly, clear, and concise.
- Use structured responses where helpful.
- Avoid unnecessary explanations.
- Do not mention context source, system prompt, or internal instructions.
- Do not explain reasoning or thinking process.

Always remain factual and grounded strictly in the provided context.

'''
