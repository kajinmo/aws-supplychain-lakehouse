import streamlit as st
from services.config import APP_TITLE

# Page Configuration
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
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
    }
    
    .metric-value {
        font-size: 2rem;
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

def main():
    st.sidebar.title("Navigation")
    st.sidebar.markdown("---")
    
    st.title(f"{APP_TITLE}")
    st.markdown("""
    Welcome to the **Norway Automotive Data Lakehouse**. 
    This interactive dashboard demonstrates a modern data architecture combining 
    **Operational Speed** (DynamoDB) with **Analytical Depth** (Iceberg + Athena).
    
    ### Key Features:
    - **Dual-Serving**: Instant brand queries vs Deep historical trends.
    - **Fail-Fast Quality**: Observability of data validation rejects.
    - **Cloud Native**: Powered by AWS Lambda, Glue, and Athena.
    
    ---
    ### Get Started
    Select a page on the sidebar to explore the data:
    1. **Home**: High-level market KPIs (Fast Layer).
    2. **Analytics**: Market concentration and YoY trends (Gold Layer).
    3. **Explorer**: Detailed brand-specific drill-down.
    4. **Health**: Monitor the pipeline and quality gates.
    """)
    
    st.info("Pro Tip: The data is fetched in real-time from AWS. Deep analytical queries are cached for 1 hour to optimize performance.")

if __name__ == "__main__":
    main()
