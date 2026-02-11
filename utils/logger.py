"""
Logging configuration for BSK Assistant
"""
import logging
import os
from config.settings import LOG_FILE

def setup_logging():
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="a",
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

def get_logger(name):
    """Get logger instance.
    Args: The name of the logger, typically the module name (e.g., __name__ for the current module)."""
    return logging.getLogger(name)