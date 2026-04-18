import os
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi

def download_kaggle_dataset(dataset_slug: str, output_path: str):
    """
    Downloads and unzips a Kaggle dataset using the official Python API.
    Professional approach for future integration with AWS Secrets Manager or SSM.
    
    Note: Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables 
    or a valid 'kaggle.json' file in ~/.kaggle/
    """
    print(f"Authenticating with Kaggle API...")
    api = KaggleApi()
    
    try:
        # This will automatically look for environment variables or the config file
        api.authenticate()
        
        print(f"Downloading dataset '{dataset_slug}' to '{output_path}'...")
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # unzip=True automatically handles the extraction of the zip file
        api.dataset_download_files(dataset_slug, path=output_path, unzip=True)
        
        print("Download and extraction completed successfully via Native API.")
    except Exception as e:
        print(f"Failed to download dataset. Ensure credentials are set properly: {e}")

if __name__ == "__main__":
    DATASET_SLUG = "dmi3kno/newcarsalesnorway"
    OUTPUT_DIR = "data"
    
    download_kaggle_dataset(DATASET_SLUG, OUTPUT_DIR)
