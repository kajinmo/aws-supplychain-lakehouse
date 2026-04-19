import argparse
import sys
import os
from pathlib import Path

# Ensure src is in python path
sys.path.append(os.path.abspath("src"))

from extract.kaggle_fetcher import download_kaggle_dataset
from extract.mock_generator import generate_mock_sales
from extract.ingestion_job import extract_and_validate
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Data Lakehouse Ingestion Pipeline")
    parser.add_argument("--mock", action="store_true", help="Run using mock generator instead of Kaggle")
    parser.add_argument("--chaos", action="store_true", help="Inject chaos into mock data (requires --mock)")
    
    args = parser.parse_args()
    
    csv_path = ""
    
    if args.mock:
        print("\n=== Running Pipeline with MOCK DATA ===")
        # Generate mock mock dataset inside data/ folder
        generate_mock_sales("data", inject_chaos=args.chaos)
        
        # We need to find the latest generated mock file
        now = datetime.now()
        mock_file = f"data/norway_mock_sales_{now.year}_{now.month}.csv"
        
        if os.path.exists(mock_file):
            csv_path = mock_file
        else:
            print("[Error] Failed to locate generated mock file.")
            sys.exit(1)
    else:
        print("\n=== Running Pipeline with KAGGLE DATA ===")
        print("Note: Ensure your Kaggle API key is set in your environment variables.")
        dataset_slug = "dmi3kno/newcarsalesnorway"
        csv_path = download_kaggle_dataset(dataset_slug, "data")
        
        if not csv_path or not os.path.exists(csv_path):
            print("[Error] Failed to retrieve dataset from Kaggle.")
            print("Try running with --mock to test the pipeline without Kaggle.")
            sys.exit(1)
            
    print("\n=== Executing Quality Gate and Bronze Segregation ===")
    extract_and_validate(csv_path)

if __name__ == "__main__":
    main()
