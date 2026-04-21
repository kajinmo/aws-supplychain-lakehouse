import streamlit as st
import plotly.express as px
from services.api_client import APIClient
from services.athena_client import AthenaClient

# Page Config
st.set_page_config(page_title="Market Overview", layout="wide")

def display_home():
    st.title("Market Overview")
    st.markdown("""
        Dual-serving interface combining **Real-time Operational Data** (DynamoDB) 
        and **Historical Analytical Trends** (Apache Iceberg & Athena).
    """)

    api = APIClient()
    athena = AthenaClient()
    
    # --- DATA FETCHING ---
    with st.spinner("Fetching operational data..."):
        all_brands = api.get_all_manufacturers()
        # Fetching a cross-section of top brands for the overview
        # In a real app, we might have a dedicated /top-brands endpoint
        top_brands_sample = ["Tesla", "Volkswagen", "Toyota", "BMW", "Volvo", "Audi", "Hyundai", "Nissan"]
        combined_data = []
        for brand in top_brands_sample:
            df = api.get_sales_by_brand(brand, year=None)
            if not df.empty:
                combined_data.append(df)
    
    if combined_data:
        full_df = pd.concat(combined_data)
        
        # --- ROW 1: KPIs ---
        c1, c2, c3 = st.columns(3)
        
        total_units = full_df["Quantity"].sum()
        c1.metric("Total Units (Top Brands)", f"{int(total_units):,}")
        
        leader = full_df.groupby("manufacturer")["Quantity"].sum().idxmax()
        c2.metric("Market Leader (Sample)", leader)
        
        avg_share = full_df["Pct"].mean()
        c3.metric("Avg. Market Share", f"{avg_share:.1f}%")
        
        st.divider()
        
        # --- ROW 2: Charts ---
        col_left, col_right = st.columns(2, gap="large")
        
        with col_left:
            st.subheader("Brand Distribution")
            fig_pie = px.pie(
                full_df.groupby("manufacturer")["Quantity"].sum().reset_index(),
                values="Quantity", 
                names="manufacturer",
                template="plotly_dark",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Blues
            )
            st.plotly_chart(fig_pie, width='stretch')
            
        with col_right:
            st.subheader("Monthly Volume Trend (Historical)")
            
            with st.spinner("Querying Athena for historical trend..."):
                # Fetching the first 36 months of the dataset (2007+) as requested
                # for the specified top brands.
                brands_str = "', '".join(top_brands_sample)
                query = f"""
                    SELECT 
                        CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR), 2, '0') as year_month, 
                        make as manufacturer, 
                        quantity
                    FROM lakehouse_db.norway_car_sales_silver
                    WHERE make IN ('{brands_str}')
                    ORDER BY year_month ASC
                    LIMIT 300
                """
                # Using 300 to cover ~36 months for 8 brands
                trend_df = athena.run_gold_query(query)
            
            if not trend_df.empty:
                # Ensure correct casing for Plotly (Athena uses different aliases sometimes, 
                # but our Silver table has quantity/manufacturer. 
                # Let's ensure consistency here.)
                trend_df = trend_df.sort_values("year_month")
                
                fig_line = px.line(
                    trend_df,
                    x="year_month",
                    y="quantity", # Athena returns lowercase from the view/table
                    color="manufacturer",
                    template="plotly_dark",
                    line_shape="spline"
                )
                
                fig_line.update_xaxes(type='category', tickangle=45)
                fig_line.update_layout(
                    hovermode="x unified",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_line, width='stretch')
                st.caption("Data source: Apache Iceberg (Silver Layer) via Amazon Athena")
            else:
                st.info("No historical data found in Athena.")

    else:
        st.warning("No operational data available for the overview.")
        st.info("Ensure the pipeline has populated the DynamoDB table.")

if __name__ == "__main__":
    import pandas as pd # Needed for the concat
    display_home()
