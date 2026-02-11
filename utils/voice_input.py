"""
Language detection utilities
"""
from utils.logger import get_logger

logger = get_logger(__name__)

def detect_language_from_text(text: str) -> str:
    """
    Detect language from transcribed text.
    Returns: 'Bengali', 'Hindi', 'English', or 'Unknown'
    """
    if not text or not text.strip():
        return "English"
    
    text_lower = text.lower().strip()
    
    # Simple heuristic-based detection (can be enhanced with ML models)
    # Check for Bengali characters (Unicode range: 0980-09FF)
    bengali_chars = any('\u0980' <= char <= '\u09FF' for char in text)
    # Check for Hindi/Devanagari characters (Unicode range: 0900-097F)
    hindi_chars = any('\u0900' <= char <= '\u097F' for char in text)
    
    if bengali_chars:
        return "Bengali"
    elif hindi_chars:
        return "Hindi"
    else:
        # Default to English for Latin script or use OpenAI for better detection
        return "English"

