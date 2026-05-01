import streamlit as st
from services.config import APP_TITLE

# Page Configuration
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

from components.style import inject_custom_css

# Inject Custom CSS for Premium Look
inject_custom_css()

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
