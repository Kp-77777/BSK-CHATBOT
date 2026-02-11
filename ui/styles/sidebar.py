"""
CSS styling for sidebar components
"""
import streamlit as st

def apply_sidebar_styles():
    """Apply custom CSS styles for sidebar components."""
    st.markdown("""
    <style>
    .sidebar-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    
    .chat-button {
        margin: 0.2rem 0;
    }
    
    .info-box {
        background: #1f77b4;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    
    .stSelectbox > label {
        font-weight: bold;
        color: #1f77b4;
    }
    
    .memory-status {
        background: #e8f5e8;
        padding: 0.5rem;
        border-radius: 5px;
        border-left: 3px solid #4caf50;
        margin: 0.5rem 0;
        font-size: 0.8rem;
    }
    </style>
    """, unsafe_allow_html=True)

SIDEBAR_CSS = """
<style>
.sidebar-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 1rem;
    font-weight: bold;
}

.chat-button {
    margin: 0.2rem 0;
}

.info-box {
    background: #1f77b4;
    padding: 1rem;
    border-radius: 8px;
    border-left: 4px solid #1f77b4;
    margin: 1rem 0;
}

.stSelectbox > label {
    font-weight: bold;
    color: #1f77b4;
}

.memory-status {
    background: #e8f5e8;
    padding: 0.5rem;
    border-radius: 5px;
    border-left: 3px solid #4caf50;
    margin: 0.5rem 0;
    font-size: 0.8rem;
}
</style>
"""
