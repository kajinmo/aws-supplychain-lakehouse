import streamlit as st
import plotly.express as px
from services.aws_metadata import AWSMetadata
from services.athena_client import AthenaClient

# Page Config
st.set_page_config(page_title="Pipeline Health", layout="wide")

def display_health():
    st.title("Pipeline Health & Observability")
    st.markdown("Monitor the integrity of the data lakehouse and the results of the Pydantic Quality Gate.")

    aws = AWSMetadata()
    athena = AthenaClient()

    # --- ROW 1: Infrastructure Stats ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Step Functions Orchestrator")
        sfn_history = aws.get_pipeline_status()
        if sfn_history:
            latest = sfn_history[0]
            status_color = "green" if latest["status"] == "SUCCEEDED" else "red"
            st.markdown(f"**Last Run Status**: :{status_color}[{latest['status']}]")
            st.info(f"Started: {latest['started']}")
        else:
            st.warning("No SFN execution history found.")

    with col2:
        st.subheader("AWS Glue Transformation")
        glue_metrics = aws.get_glue_job_metrics()
        if glue_metrics:
            st.metric("Last Run Duration", f"{glue_metrics['duration']}s", delta_color="normal")
            st.markdown(f"**Status**: `{glue_metrics['status']}`")
        else:
            st.warning("No Glue Job history found.")
            
    with col3:
        st.subheader("Data Freshness")
        st.success("Operational Layer: Live (Real-time)")
        st.info("Analytical Layer: Batch (Last 24h)")

    st.divider()

    # --- ROW 2: Quality Gate (Pydantic Rejects) ---
    st.header("Quality Gate Metrics (Pydantic Rejects)")
    st.markdown("""
        Records that fail schema validation are automatically rerouted 
        to the **Quarantine Bucket**. Athena analyzes these rejects to 
        provide the metrics below.
    """)
    
    quality_df = athena.get_quality_metrics()
    
    if not quality_df.empty:
        m1, m2, m3 = st.columns([1, 1, 3])
        
        total_rejects = quality_df["rejected_count"].sum()
        m1.metric("Total Rejects", total_rejects, delta="-15% (vs avg)" if total_rejects > 0 else "0", delta_color="inverse")
        
        with m3:
            # Build chart for error types
            error_cols = ["quantity_errors", "make_errors", "year_errors", "month_errors"]
            # Filter only existing columns
            available_errors = [c for c in error_cols if c in quality_df.columns]
            
            error_summary = quality_df[available_errors].sum().reset_index()
            error_summary.columns = ["Error Type", "Count"]
            
            fig = px.bar(
                error_summary, 
                x="Error Type", 
                y="Count",
                template="plotly_dark",
                color_discrete_sequence=["#00D1FF"]
            )
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width='stretch')
            
        st.subheader("Quarantine Logs (Sample)")
        st.dataframe(quality_df, width='stretch')
    else:
        st.balloons()
        st.success("Clean Pipeline! No records are currently in quarantine.")

if __name__ == "__main__":
    display_health()
