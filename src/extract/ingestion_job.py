import pandas as pd
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from pydantic import ValidationError

# Ensure we can import from src
sys.path.append(os.path.abspath("src"))
from models.car_sales import CarSalesAnalytical, CarSalesApplication

def extract_and_validate(csv_path: str):
    """
    Reads the Norway Car Sales dataset, validates against the Pydantic contract (Bronze Gate),
    and separates records into Bronze (Pass) and Quarantine (Fail) layers.
    """
    print(f"[Ingestion] Reading dataset: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[Error] Failed to read CSV: {e}")
        return

    valid_analytical = []
    quarantine_records = []
    
    for index, row in df.iterrows():
        row_dict = row.to_dict()
        
        # Bronze Quality Gate - Fail-Fast
        try:
            # We validate the row. If it passes, it is ready for Bronze.
            # Using alias mapping provided by Pydantic
            analytical_model = CarSalesAnalytical(**row_dict)
            valid_analytical.append(analytical_model.model_dump())
            
        except ValidationError as e:
            # Add error reasons to the row
            # Simplify error message to fit in a string column easily
            error_msgs = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in e.errors()])
            row_dict['validation_errors'] = error_msgs
            quarantine_records.append(row_dict)
            
    # Process valid records
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = Path("data")
    
    if valid_analytical:
        bronze_dir = base_dir / "bronze" / f"ingestion_date={timestamp[:8]}"
        bronze_dir.mkdir(parents=True, exist_ok=True)
        
        df_valid = pd.DataFrame(valid_analytical)
        bronze_path = bronze_dir / f"valid_sales_{timestamp}.parquet"
        df_valid.to_parquet(bronze_path, index=False)
        print(f"[Success] Saved {len(valid_analytical)} valid records to Bronze Layer: {bronze_path}")
    else:
        print("[Warning] No valid records found.")
        
    if quarantine_records:
        quar_dir = base_dir / "quarantine" / f"ingestion_date={timestamp[:8]}"
        quar_dir.mkdir(parents=True, exist_ok=True)
        
        df_quar = pd.DataFrame(quarantine_records)
        quar_path = quar_dir / f"malformed_sales_{timestamp}.parquet"
        # Convert all to string to avoid Parquet type inference issues with mixed types in quarantine
        df_quar = df_quar.astype(str)
        df_quar.to_parquet(quar_path, index=False)
        print(f"[Dead Letter] Saved {len(quarantine_records)} invalid records to Quarantine: {quar_path}")
        
    print(f"\n[Summary] Processed {len(df)} rows.")
    print(f" - Valid (Bronze): {len(valid_analytical)}")
    print(f" - Malformed (Quarantine): {len(quarantine_records)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest and Validate Car Sales Data")
    parser.add_argument("csv_path", type=str, help="Path to the source CSV file")
    args = parser.parse_args()
    
    extract_and_validate(args.csv_path)
