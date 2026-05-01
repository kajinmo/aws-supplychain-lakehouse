import streamlit as st

def render_metric_card(title: str, value: str):
    """Renders a premium HTML card for KPIs."""
    html_content = f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{title}</div>
    </div>
    """
    st.markdown(html_content, unsafe_allow_html=True)
