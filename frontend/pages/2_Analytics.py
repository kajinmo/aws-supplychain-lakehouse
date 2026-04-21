import streamlit as st
import plotly.express as px
from services.athena_client import AthenaClient

# Page Config
st.set_page_config(page_title="Deep Analytics", layout="wide")

def display_analytics():
    st.title("Strategic Analytics (Gold Layer)")
    st.markdown("Deep historical insights calculated via **Apache Iceberg & Amazon Athena**.")

    athena = AthenaClient()
    
    # Year Selector
    selected_year = st.sidebar.slider("Select Analysis Year", 2007, 2027, 2026)

    # --- ROW 1: Market Leaders & Concentration ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader(f"Top 10 Market Leaders ({selected_year})")
        leaders_df = athena.run_gold_query(f"SELECT * FROM gold_market_leaders WHERE year = {selected_year} LIMIT 10")
        if not leaders_df.empty:
            fig_leaders = px.bar(
                leaders_df, 
                x="total_units", 
                y="make", 
                orientation='h',
                color="total_market_share",
                template="plotly_dark",
                color_continuous_scale="Viridis",
                labels={"make": "Manufacturer", "total_units": "Units Sold"}
            )
            fig_leaders.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_leaders, width='stretch')
        else:
            st.info("No data found for this year in the Gold Layer.")

    with col_right:
        st.subheader("Market Concentration (HHI Index)")
        concentration_df = athena.run_gold_query("SELECT * FROM gold_brand_concentration ORDER BY year ASC")
        if not concentration_df.empty:
            fig_hhi = px.area(
                concentration_df,
                x="year",
                y="hhi_index",
                template="plotly_dark",
                color_discrete_sequence=["#00D1FF"]
            )
            # Add HHI threshold lines
            fig_hhi.add_hline(y=1500, line_dash="dash", line_color="green", annotation_text="Competitive")
            fig_hhi.add_hline(y=2500, line_dash="dash", line_color="red", annotation_text="Concentrated")
            st.plotly_chart(fig_hhi, width='stretch')
            st.caption("Lower HHI = More Competitive Market. Higher HHI = Dominance by few brands.")


    st.divider()

    # --- ROW 2: Growth & Emerging Brands ---
    cl, cr = st.columns(2)
    
    with cl:
        st.subheader("YoY Growth Winners")
        growth_df = athena.get_yoy_growth(selected_year)
        if not growth_df.empty:
            # Filter top 10 growers
            top_growth = growth_df.nlargest(10, "yoy_growth_pct")
            fig_growth = px.bar(
                top_growth,
                x="yoy_growth_pct",
                y="make",
                template="plotly_dark",
                color="yoy_growth_pct",
                color_continuous_scale="RdYlGn"
            )
            st.plotly_chart(fig_growth, width='stretch')
        else:
            st.info("YoY comparison requires data from the previous year.")

    with cr:
        st.subheader("Emerging Disruptors (Since 2015)")
        emerging_df = athena.run_gold_query(f"SELECT * FROM gold_emerging_brands WHERE year = {selected_year} ORDER BY total_units DESC LIMIT 8")
        if not emerging_df.empty:
            # Use a scatter/bubble plot for emerging brands
            fig_emerging = px.scatter(
                emerging_df,
                x="make",
                y="total_units",
                size="total_units",
                color="yoy_growth_pct",
                hover_name="make",
                template="plotly_dark",
                size_max=40
            )
            st.plotly_chart(fig_emerging, width='stretch')
        else:
            st.info("No emerging brands found in the dataset for this period.")

if __name__ == "__main__":
    display_analytics()
