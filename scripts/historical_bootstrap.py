import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

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
    logger.error(f"Failed to import project modules. Ensure you are running from project root. Details: {e}")
    sys.exit(1)

# Set environment variables for the ingestion_job to point to the Cloud
os.environ["BRONZE_BUCKET"] = BUCKET_BRONZE
os.environ["QUARANTINE_BUCKET"] = BUCKET_QUARANTINE

def bootstrap_history():
    """
    Downloads historical Kaggle data and pushes it to the S3 Bronze bucket
    after validating it through the Pydantic Quality Gate.
    """
    logger.info("="*40)
    logger.info("HISTORICAL DATA BOOTSTRAP")
    logger.info("="*40)
    logger.info(f"Targeting S3 (Bronze): {BUCKET_BRONZE}")
    logger.info(f"Targeting S3 (Quarantine): {BUCKET_QUARANTINE}")
    logger.info("-" * 40)
    
    # 1. Download Kaggle Dataset
    dataset_slug = "dmi3kno/newcarsalesnorway"
    logger.info(f"[1/2] Fetching historical dataset: {dataset_slug}...")
    
    csv_path = download_kaggle_dataset(dataset_slug, "data")
    
    if not csv_path or not os.path.exists(csv_path):
        logger.error("Failed to download Kaggle dataset.")
        logger.warning("Note: Ensure KAGGLE_USERNAME and KAGGLE_KEY are set.")
        return

    # 2. Extract, Validate and Push to S3
    logger.info("[2/2] Running Quality Gate and Pushing to Cloud...")
    try:
        results = extract_and_validate(csv_path)
        
        logger.info("="*40)
        logger.info("BOOTSTRAP COMPLETED SUCCESSFULLY")
        logger.info("="*40)
        logger.info(f"Total Processed: {results['processed']}")
        logger.info(f"Uploaded to Bronze (S3): {results['valid']}")
        logger.info(f"Sent to Quarantine (S3): {results['quarantined']}")
        logger.info("-" * 40)

    except Exception as e:
        logger.error(f"Failed during validation/upload: {e}")
        logger.warning("Note: Ensure your AWS credentials are set properly.")

if __name__ == "__main__":
    bootstrap_history()
