"""
Complete System Initialization
Runs all required initialization steps for first-time setup
"""
import os
import sys
from dotenv import load_dotenv
from utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

def run_full_initialization():
    """Run all initialization steps."""
    try:
        logger.info("=" * 70)
        logger.info("INITIALIZING BSK ASSISTANT SYSTEM")
        logger.info("=" * 70)
        
        # Step 1: Initialize MongoDB
        logger.info("\n[1/4] Initializing MongoDB...")
        from scripts.initialize_mongodb import initialize_mongodb
        mongo_success = initialize_mongodb()
        
        if not mongo_success:
            logger.warning("⚠ MongoDB initialization had issues (may continue)")
        
        # Step 2: Initialize Chroma
        logger.info("\n[2/4] Initializing Chroma Vector Store...")
        from scripts.initialize_chroma import initialize_chroma
        chroma_success = initialize_chroma()
        
        if not chroma_success:
            logger.warning("⚠ Chroma initialization had issues (may continue)")
        
        # Step 3: Check Ollama
        logger.info("\n[3/4] Checking Ollama Service...")
        from scripts.check_ollama import check_ollama_health
        ollama_success = check_ollama_health()
        
        if not ollama_success:
            logger.warning("⚠ Ollama check had issues (install/start Ollama and pull models)")
        
        # Step 4: Run application checks
        logger.info("\n[4/4] Running Application Checks...")
        from core.initialization import ServiceInitializer
        results, critical_passed = ServiceInitializer.run_all_checks(exit_on_failure=False)
        
        logger.info("=" * 70)
        logger.info("INITIALIZATION SUMMARY")
        logger.info("=" * 70)
        
        if critical_passed:
            logger.info("✓ All critical services initialized successfully!")
            logger.info("\nYou can now start the application:")
            logger.info("  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
            logger.info("  streamlit run ui/pages/chatbot.py")
            return True
        else:
            logger.warning("\n⚠ Some services are not available.")
            logger.warning("Please check the logs above and fix any issues.")
            return False
            
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = run_full_initialization()
    sys.exit(0 if success else 1)
