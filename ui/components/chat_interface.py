"""
Enhanced Chat interface components with UUID-based chat management
"""
import streamlit as st
import time
from datetime import datetime
from core.rag_engine import rag_engine
from services.chat_service import chat_service
from utils.logger import get_logger


logger = get_logger(__name__)

def _render_empty_chat_placeholder():
    """Render placeholder for empty chats."""
    if len(st.session_state.get('current_chat_messages', [])) == 0:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #666;">
            <h3>📝 No messages in this chat yet</h3>
            <p>Start a conversation to see messages here</p>
        </div>
        """, unsafe_allow_html=True)

def render_chat_messages():
    """Render chat messages with clean display."""
    messages = st.session_state.get('current_chat_messages', [])

    if messages:
        for message in messages:
            role = message["role"]
            content = message["content"]
            
            # Choose avatar based on role
            if role == "user":
                avatar = "👤"
            elif role == "Virtual Assistant":
                avatar = "🏛️"
            else:
                avatar = "🤖"
            
            with st.chat_message(role, avatar=avatar):
                st.write(content)
    else:
        _render_empty_chat_placeholder()

def _create_new_chat_if_needed():
    """Create a new chat if in pending state."""
    if st.session_state.get('pending_new_chat', False):
        new_chat_id = chat_service.create_new_chat()
        st.session_state.current_chat_id = new_chat_id
        st.session_state.current_chat_messages = []
        st.session_state.is_new_chat = True
        st.session_state.pending_new_chat = False
        
        logger.info(f"Created new chat with UUID: {new_chat_id}")
        return new_chat_id
    
    return st.session_state.get('current_chat_id')

def _handle_user_query(user_query):
    """Handle user query processing with enhanced memory management."""
    try:
        # Create a new chat if in pending state
        current_chat_id = _create_new_chat_if_needed()
        
        if not current_chat_id:
            st.error("Failed to create or access chat. Please try again.")
            return

        # Save user message to DB first
        if not chat_service.save_message_to_chat(current_chat_id, "user", user_query):
            st.error("Failed to save message. Please try again.")
            return

        # Ensure session messages list exists
        if 'current_chat_messages' not in st.session_state:
            st.session_state.current_chat_messages = []

        # Create user message with enhanced metadata
        user_message = {
            "role": "user",
            "content": user_query,
            "timestamp": datetime.now().isoformat(),
            "chat_id": current_chat_id
        }

        # Append user message immediately
        st.session_state.current_chat_messages.append(user_message)

        # Update chat title on first message
        if st.session_state.get('is_new_chat', False):
            chat_service.update_chat_title(current_chat_id, user_query)
            st.session_state.is_new_chat = False

        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.write(user_query)

        # Process and display assistant response
        with st.chat_message("assistant", avatar="🏛️"):
            response_placeholder = st.empty()
            full_response = ""

            with st.spinner("🤔 Thinking..."):
                try:
                    for chunk in rag_engine.process_query(user_query, chat_id=current_chat_id):
                        full_response += chunk
                        response_placeholder.markdown(full_response)
                except Exception as e:
                    logger.error(f"RAG processing error: {e}")
                    full_response = "I apologize, but I encountered an error while processing your question. Please try again or rephrase your query."
                    response_placeholder.markdown(full_response)

            # Save assistant response
            if chat_service.save_message_to_chat(current_chat_id, "Virtual Assistant", full_response):
                assistant_message = {
                    "role": "Virtual Assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                    "chat_id": current_chat_id
                }
                st.session_state.current_chat_messages.append(assistant_message)
                logger.info(f"Saved assistant response to chat {current_chat_id}")
            else:
                logger.error(f"Failed to save assistant response to chat {current_chat_id}")

        # Update memory loaded flag
        st.session_state.memory_loaded_for_chat = current_chat_id

        # Trigger re-render to update message list and move input bar back to bottom
        st.rerun()

    except Exception as e:
        logger.error(f"Error handling user query: {e}")
        st.error("⚠️ An error occurred while processing your query. Please try again.")
        st.exception(e)

def render_chat_input():
    """Render chat input + mic fixed at the bottom."""
    current_chat_id = st.session_state.get('current_chat_id')
    is_new_chat = st.session_state.get('is_new_chat', False)
    pending_new_chat = st.session_state.get('pending_new_chat', False)

    # Only show warning if not in pending state and no current chat
    if not pending_new_chat and not current_chat_id and not is_new_chat:
        st.warning("Please select or create a chat first")
        return

    # Chat input
    with st.container():
        user_query = st.chat_input("💬 Ask your question about BSK services...")

        if user_query:
            _handle_user_query(user_query)
