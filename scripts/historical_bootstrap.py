import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to sys.path to allow imports from our project structure
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(project_root, "src"))
sys.path.append(project_root)

try:
    from extract.kaggle_fetcher import download_kaggle_dataset
    from extract.ingestion_job import extract_and_validate
    from frontend.services.config import BUCKET_BRONZE, BUCKET_QUARANTINE
except ImportError as e:
    print(f"[Error] Failed to import project modules. Ensure you are running from project root. Details: {e}")
    sys.exit(1)

# Set environment variables for the ingestion_job to point to the Cloud
os.environ["BRONZE_BUCKET"] = BUCKET_BRONZE
os.environ["QUARANTINE_BUCKET"] = BUCKET_QUARANTINE

def bootstrap_history():
    """
    Downloads historical Kaggle data and pushes it to the S3 Bronze bucket
    after validating it through the Pydantic Quality Gate.
    """
    print("\n" + "="*40)
    print("HISTORICAL DATA BOOTSTRAP")
    print("="*40)
    print(f"Targeting S3 (Bronze): {BUCKET_BRONZE}")
    print(f"Targeting S3 (Quarantine): {BUCKET_QUARANTINE}")
    print("-" * 40)
    
    # 1. Download Kaggle Dataset
    dataset_slug = "dmi3kno/newcarsalesnorway"
    print(f"[1/2] Fetching historical dataset: {dataset_slug}...")
    
    csv_path = download_kaggle_dataset(dataset_slug, "data")
    
    if not csv_path or not os.path.exists(csv_path):
        print("\n[Error] Failed to download Kaggle dataset.")
        print("Note: Ensure KAGGLE_USERNAME and KAGGLE_KEY are set.")
        return

    # 2. Extract, Validate and Push to S3
    print(f"\n[2/2] Running Quality Gate and Pushing to Cloud...")
    try:
        results = extract_and_validate(csv_path)
        
        print("\n" + "="*40)
        print("BOOTSTRAP COMPLETED SUCCESSFULLY")
        print("="*40)
        print(f"Total Processed: {results['processed']}")
        print(f"Uploaded to Bronze (S3): {results['valid']}")
        print(f"Sent to Quarantine (S3): {results['quarantined']}")
        print("-" * 40)
        print("\nNEXT STEPS:")
        print("1. Go to the AWS Console -> Step Functions.")
        print(f"2. Start a manual execution of: 'car-sales-lakehouse-batch-orchestrator'")
        print("3. Wait for the Glue Job to finish (The Split).")
        print("4. Check your Streamlit Dashboard!")
        print("="*40 + "\n")

    except Exception as e:
        print(f"\n[Error] Failed during validation/upload: {e}")
        print("Note: Ensure your AWS credentials are set properly.")

if __name__ == "__main__":
    bootstrap_history()
