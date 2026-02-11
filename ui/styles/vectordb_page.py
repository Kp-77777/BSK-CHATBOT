"""
CSS styling for vector operations page
"""
import streamlit as st

def apply_vector_operations_styling():
    """Apply custom CSS styling for vector operations page with dark navy theme and teal accents."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Title and header styling */
    h1, h2, h3 {
        color: #4DD0E1;
        margin-bottom: 1rem;
    }
    
    /* Statistics cards */
    div[data-testid="stMetric"] {
        background-color: rgba(30, 40, 67, 0.6);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        transition: transform 0.2s;
        border: 1px solid rgba(77, 208, 225, 0.2);
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        border: 1px solid rgba(77, 208, 225, 0.5);
    }
    
    div[data-testid="stMetric"] label {
        font-weight: bold;
        color: #4DD0E1;
    }
    
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #E0F7FA;
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.2s;
        background-color: rgba(30, 40, 80, 0.6);
        border: 1px solid rgba(77, 208, 225, 0.3);
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        border: 1px solid rgba(77, 208, 225, 0.8);
    }
    
    /* Primary button emphasis */
    .stButton button[kind="primary"] {
        background-color: #00ACC1;
        color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.4);
    }
    
    /* Radio button styling */
    .stRadio > div {
        background-color: rgba(30, 40, 67, 0.3);
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    .stRadio label {
        color: #4DD0E1;
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        background-color: rgba(30, 40, 67, 0.6);
        border: 1px solid rgba(77, 208, 225, 0.3);
        border-radius: 6px;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        background-color: rgba(30, 40, 67, 0.6);
        border: 1px solid rgba(77, 208, 225, 0.3);
        border-radius: 6px;
        color: #E0F7FA;
    }
    
    .stTextInput > div > div > input:focus {
        border: 1px solid rgba(77, 208, 225, 0.8);
        box-shadow: 0 0 0 2px rgba(77, 208, 225, 0.2);
    }
    
    /* Checkbox styling */
    .stCheckbox > label {
        color: #4DD0E1;
    }
    
    /* Container styling for better spacing */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Status messages */
    .element-container div[data-baseweb="notification"] {
        border-radius: 8px;
        margin-bottom: 1rem;
        background-color: rgba(30, 40, 67, 0.7);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #4DD0E1;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: rgba(30, 40, 67, 0.4);
    }
    
    .stFileUploader label {
        color: #4DD0E1;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: rgba(20, 30, 55, 0.3);
    }
    
    .stTabs [role="tab"] {
        padding: 0.5rem 1rem;
        color: #4DD0E1;
    }
    
    .stTabs [role="tab"][aria-selected="true"] {
        background-color: rgba(77, 208, 225, 0.2);
        font-weight: bold;
        border-bottom: 2px solid #4DD0E1;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #4DD0E1;
    }
    
    /* Progress bar */
    div[data-testid="stProgress"] > div {
        background-color: #4DD0E1;
    }
    
    /* Horizontal dividers */
    hr {
        margin: 2rem 0;
        border-color: rgba(77, 208, 225, 0.2);
    }
    
    /* Success/error messages */
    .stSuccess {
        background-color: rgba(76, 175, 80, 0.3);
        border: 1px solid rgba(76, 175, 80, 0.6);
    }
    
    .stInfo {
        background-color: rgba(0, 172, 193, 0.3);
        border: 1px solid rgba(0, 172, 193, 0.6);
    }
    
    .stWarning {
        background-color: rgba(255, 152, 0, 0.3);
        border: 1px solid rgba(255, 152, 0, 0.6);
    }
    
    .stError {
        background-color: rgba(244, 67, 54, 0.3);
        border: 1px solid rgba(244, 67, 54, 0.6);
    }
    
    /* Code blocks */
    code, pre {
        background-color: rgba(20, 30, 55, 0.7);
        border-radius: 4px;
        border: 1px solid rgba(77, 208, 225, 0.2);
    }
    
    /* Custom container for document items */
    .document-item {
        border: 1px solid rgba(77, 208, 225, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        background-color: rgba(30, 40, 67, 0.3);
    }
    
    /* File list styling */
    .file-list-item {
        background-color: rgba(30, 40, 67, 0.4);
        border-radius: 6px;
        padding: 0.5rem;
        margin-bottom: 0.25rem;
        border-left: 3px solid #4DD0E1;
    }
    </style>
    """, unsafe_allow_html=True)