"""
BSK Assistant - Main Application Entry Point (Streamlit App)
"""
import streamlit as st
from ui.pages.chatbot import show_chatbot_page
from ui.pages.vector_operations import show_vector_operations_page
from config.settings import PAGE_CONFIG
from utils.logger import setup_logging, get_logger
from core.initialization import initialize_app

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Initialize app on startup
if "app_initialized" not in st.session_state:
    logger.info("Initializing BSK Assistant Application...")
    initialize_results = initialize_app()
    st.session_state.app_initialized = True
    st.session_state.init_results = initialize_results

# Configure page settings
st.set_page_config(**PAGE_CONFIG)

def main():
    """Main application entry point."""
    # Initialize session state for current page
    if "current_page" not in st.session_state:
        st.session_state.current_page = "chat"
        logger.info("Initialized session state with default page: chat")
    
    # Get current page from session state
    current_page = st.session_state.get("current_page", "chat")  #gets chat as default
    logger.debug(f"Current page: {current_page}")
    
    # Route to appropriate page based on session state
    if current_page == "chat":
        show_chatbot_page()
    elif current_page == "vector_ops":
        show_vector_operations_page()
    else:
        # Default to chat page if unknown page
        logger.warning(f"Unknown page: {current_page}, defaulting to chat")
        st.session_state.current_page = "chat"
        show_chatbot_page()

if __name__ == "__main__":
    main()