import pandas as pd
import sys
import os
sys.path.append(os.path.abspath("src"))

from typing import List, Dict, Any
from pydantic import ValidationError
from models.car_sales import CarSalesAnalytical, CarSalesApplication

def extract_and_validate(csv_path: str):
    """
    Reads the Norway Car Sales dataset, validates against the Pydantic contract (Bronze Gate),
    and demonstrates transformation to the Operational Layer (DynamoDB schema).
    """
    print(f"Reading dataset: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    valid_analytical = []
    operational_ready = []
    quarantine_records = []
    
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        
        # 1. Pydantic validation (Bronze Quality Gate - Fail-Fast)
        try:
            # The model uses aliases to match 'Year', 'Month', 'Make', etc.
            analytical_model = CarSalesAnalytical(**row_dict)
            valid_analytical.append(analytical_model.model_dump())
            
            # 2. Transformation to Operational Layer (Application Model)
            # Synthesis of PK and SK for DynamoDB
            # manufacturer = make
            # year_month = YYYY-MM
            year_month = f"{analytical_model.year}-{str(analytical_model.month).zfill(2)}"
            
            app_model = CarSalesApplication(
                manufacturer=analytical_model.make,
                year_month=year_month,
                quantity=analytical_model.quantity,
                market_share_pct=analytical_model.pct
            )
            operational_ready.append(app_model.model_dump())
            
        except ValidationError as e:
            row_dict['validation_errors'] = str(e)
            quarantine_records.append(row_dict)
            
    print(f"Processed {len(df)} rows.")
    print(f"Valid records (Bronze Layer): {len(valid_analytical)}")
    print(f"Operational records (Ready for DynamoDB): {len(operational_ready)}")
    print(f"Quarantined records (Dead Letter): {len(quarantine_records)}")

if __name__ == "__main__":
    extract_and_validate("data/norway_new_car_sales_by_make.csv")
