import os
from pathlib import Path

def download_kaggle_dataset(dataset_slug: str, output_path: str) -> str:
    from kaggle.api.kaggle_api_extended import KaggleApi

    """
    Downloads and unzips a Kaggle dataset using the official Python API.
    Returns the path to the main CSV file for our pipeline.
    
    Note: Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables 
    or a valid 'kaggle.json' file in ~/.kaggle/
    """
    print(f"[Kaggle] Authenticating with Kaggle API...")
    api = KaggleApi()
    
    try:
        # This will automatically look for environment variables or the config file
        api.authenticate()
        
        print(f"[Kaggle] Downloading dataset '{dataset_slug}' to '{output_path}'...")
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # unzip=True automatically handles the extraction of the zip file
        api.dataset_download_files(dataset_slug, path=output_path, unzip=True)
        
        print("[Kaggle] Download and extraction completed successfully.")
        
        # We need the Make dataset for our pipeline
        dataset_csv = os.path.join(output_path, "norway_new_car_sales_by_make.csv")
        
        if os.path.exists(dataset_csv):
            return dataset_csv
        else:
            print("[Warning] Expected CSV not found. Returning output path.")
            return output_path
            
    except Exception as e:
        print(f"[Error] Failed to download dataset. Ensure credentials are set properly: {e}")
        return ""

if __name__ == "__main__":
    DATASET_SLUG = "dmi3kno/newcarsalesnorway"
    OUTPUT_DIR = "data"
    
    download_kaggle_dataset(DATASET_SLUG, OUTPUT_DIR)
