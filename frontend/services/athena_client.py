import boto3
import pandas as pd
import time
import streamlit as st
from .config import (
    AWS_REGION, 
    ATHENA_DATABASE, 
    ATHENA_WORKGROUP, 
    ATHENA_RESULT_BUCKET
)

class AthenaClient:
    """Service to interact with the Analytical Gold Layer (Athena)."""

    def __init__(self):
        self.client = boto3.client("athena", region_name=AWS_REGION)

    @st.cache_data(ttl=3600)  # Cache results for 1 hour to optimize costs
    def run_gold_query(_self, query: str):
        """
        Execute an Athena query and return results as a Pandas DataFrame.
        Uses Streamlit cache to prevent redundant S3 scans.
        """
        try:
            response = _self.client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={"Database": ATHENA_DATABASE},
                WorkGroup=ATHENA_WORKGROUP,
            )
            query_execution_id = response["QueryExecutionId"]

            # Simple polling until completion
            while True:
                status = _self.client.get_query_execution(
                    QueryExecutionId=query_execution_id
                )["QueryExecution"]["Status"]["State"]
                
                if status == "SUCCEEDED":
                    break
                elif status in ["FAILED", "CANCELLED"]:
                    raise Exception(f"Athena query failed with status: {status}")
                
                time.sleep(0.5)

            # Fetch results using get_query_results or pagination
            # For simplicity in this portfolio, we use a helper to read the CSV from S3 results bucket
            # or directly from Athena get_query_results (for small results < 1000 rows)
            
            results = _self.client.get_query_results(QueryExecutionId=query_execution_id)
            
            column_names = [col["Name"] for col in results["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
            rows = []
            
            # Skip header row
            for row in results["ResultSet"]["Rows"][1:]:
                rows.append([data.get("VarCharValue") for data in row["Data"]])
            
            df = pd.DataFrame(rows, columns=column_names)
            
            # Automatic numeric conversion for common analytical columns
            numeric_cols = ["total_units", "ranking", "yoy_growth_pct", "total_market_share", "hhi_index", "rejected_count"]
            for col in df.columns:
                if any(x in col for x in numeric_cols):
                    df[col] = pd.to_numeric(df[col], errors="ignore")
                    
            return df

        except Exception as e:
            st.error(f"Error querying Gold Layer: {e}")
            return pd.DataFrame()
            
    def get_market_leaders(self, year: int = 2023):
        return self.run_gold_query(f"SELECT * FROM gold_market_leaders WHERE year = {year} ORDER BY ranking ASC")

    def get_yoy_growth(self, year: int = 2023):
        return self.run_gold_query(f"SELECT * FROM gold_yoy_growth WHERE year = {year} ORDER BY yoy_growth_pct DESC")

    def get_quality_metrics(self):
        return self.run_gold_query("SELECT * FROM gold_quality_metrics ORDER BY ingestion_date DESC")
