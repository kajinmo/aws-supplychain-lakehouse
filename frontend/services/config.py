"""
Centralized configuration for the Streamlit Frontend.
Stores API endpoints, AWS resource names, and UI constants.
"""

# API Gateway Endpoint (from Epic 6)
API_BASE_URL = "https://oforctm94m.execute-api.us-east-1.amazonaws.com"

# AWS Geography & Names
AWS_REGION = "us-east-1"
ATHENA_DATABASE = "lakehouse_db"
ATHENA_WORKGROUP = "car-sales-lakehouse-workgroup"
ATHENA_RESULT_BUCKET = "car-sales-lakehouse-athena-results-324037321692"

# S3 Buckets (Observability)
BUCKET_BRONZE = "car-sales-lakehouse-bronze-324037321692"
BUCKET_QUARANTINE = "car-sales-lakehouse-quar-324037321692"

# State Machine (Pipeline Health)
SFN_NAME = "car-sales-lakehouse-batch-orchestrator"
GLUE_JOB_NAME = "car-sales-lakehouse-the-split-job"

# UI Constants
APP_TITLE = "Norway Car Sales | Data Lakehouse"
