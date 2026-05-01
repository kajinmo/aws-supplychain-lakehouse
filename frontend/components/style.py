import streamlit as st

def inject_custom_css():
    """Injects premium CSS aesthetics across all Streamlit pages."""
    st.markdown("""
        <style>
        /* Main Background and Font */
        .stApp {
            background-color: #0E1117;
        }
        
        /* Premium KPI Cards (Glassmorphism Lite) */
        .metric-card {
            background-color: #161B22;
            border: 1px solid #30363D;
            padding: 20px;
            border-radius: 10px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            margin-bottom: 1rem;
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: bold;
            color: #00D1FF;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: #8B949E;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #161B22;
            border-right: 1px solid #30363D;
        }
        
        /* Header Customization */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #FFFFFF !important;
        }
        
        /* Gradient Button */
        .stButton>button {
            background: linear-gradient(90deg, #00D1FF 0%, #0077FF 100%);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .stButton>button:hover {
            transform: scale(1.05);
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
