import pandas as pd
import json

def analyze():
    """
    Exploratory script to inspect raw data and understand the schema
    of the Norway Car Sales dataset.
    """
    print("Reading norway_new_car_sales_by_make.csv dataset...")
    try:
        # Read a small sample for local exploration
        df = pd.read_csv("data/norway_new_car_sales_by_make.csv")
        
        print("\n[INFO] Columns found:")
        for col in df.columns:
            print(f" - {col}")
            
        print("\n[INFO] Sample of 2 records (Raw JSON):")
        sample_records = df.head(2).to_dict(orient="records")
        print(json.dumps(sample_records, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    analyze()
