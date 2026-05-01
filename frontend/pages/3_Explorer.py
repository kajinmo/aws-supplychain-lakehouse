import streamlit as st
import plotly.express as px
from services.api_client import APIClient
from services.athena_client import AthenaClient
from components.style import inject_custom_css
from components.cards import render_metric_card

# Page Config
st.set_page_config(page_title="Brand Explorer", layout="wide")

@st.cache_data(ttl=3600)
def fetch_all_brands():
    return APIClient().get_all_manufacturers()

@st.cache_data(ttl=3600)
def fetch_brand_data(brand, year):
    return APIClient().get_sales_by_brand(brand, year=year)

def display_explorer():
    inject_custom_css()
    
    st.title("Brand Explorer")
    st.markdown("Search and analyze specific manufacturer performance in the Norway market.")

    # --- Sidebar: Search Filters ---
    st.sidebar.header("Search Filters")
    with st.spinner("Loading brands..."):
        all_brands = fetch_all_brands()
    
    if not all_brands:
        st.error("Could not fetch brands from the Operational API. Ensure the table is populated.")
        return

    # User Selects Brand
    selected_brand = st.sidebar.selectbox(
        "Select Manufacturer", 
        all_brands,
        index=all_brands.index("Tesla") if "Tesla" in all_brands else 0
    )
    
    # Year Filter
    min_y, max_y = AthenaClient().get_min_max_years()
    selected_year = st.sidebar.select_slider("Focus Year (Optional)", options=[None] + list(range(min_y, max_y + 1)))

    # --- Data Fetching ---
    with st.spinner(f"Analyzing {selected_brand}..."):
        df = fetch_brand_data(selected_brand, year=selected_year)

    if not df.empty:
        # --- ROW 1: Brand KPIs ---
        col1, col2, col3 = st.columns(3)
        
        total_units = df["Quantity"].sum()
        with col1:
            render_metric_card(f"Total Units ({selected_brand})", f"{int(total_units):,}")
        
        avg_share = df["Pct"].mean()
        with col2:
            render_metric_card("Avg. Market Share", f"{avg_share:.2f}%")
        
        peak_month = df.loc[df["Quantity"].idxmax(), "year_month"]
        with col3:
            render_metric_card("Best Month", peak_month)

        st.divider()

        # --- ROW 2: Chronological Performance ---
        st.subheader(f"Volume Trend: {selected_brand}")
        fig_vol = px.line(
            df,
            x="year_month",
            y="Quantity",
            template="plotly_dark",
            line_shape="spline",
            color_discrete_sequence=["#00D1FF"],
            markers=True
        )
        fig_vol.update_layout(hovermode="x unified")
        st.plotly_chart(fig_vol, width='stretch')

        # --- ROW 3: Market Share Stability ---
        st.subheader(f"Market Share % Trend: {selected_brand}")
        fig_share = px.area(
            df,
            x="year_month",
            y="Pct",
            template="plotly_dark",
            color_discrete_sequence=["#0077FF"],
            labels={"Pct": "Market Share %"}
        )
        st.plotly_chart(fig_share, width='stretch')

        # Raw Data Expander
        with st.expander("View Raw Sales Data"):
            st.dataframe(df, width='stretch')

    else:
        st.warning(f"No records found for **{selected_brand}** in the selected period.")

if __name__ == "__main__":
    display_explorer()
