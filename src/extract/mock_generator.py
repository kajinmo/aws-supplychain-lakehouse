import csv
import random
import os
from datetime import datetime

# Top car brands in Norway to simulate real-world data
BRANDS = [
    "Volkswagen", "Toyota", "Tesla", "Volvo", "Skoda", 
    "BMW", "Audi", "Nissan", "Ford", "Kia", "Hyundai", "BYD"
]

def generate_mock_sales(output_dir: str = "data", inject_chaos: bool = False):
    """
    Simulates a daily/monthly data ingestion job by generating random car sales data.
    If inject_chaos is True, it will purposefully create some malformed records
    to test the Pydantic Quality Gate (e.g. Negative Quantities, Missing Make).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Generate a random total market size for the month
    total_market_sales = random.randint(8000, 15000)
    
    filename = os.path.join(output_dir, f"norway_mock_sales_{year}_{month}.csv")
    
    records = []
    accumulated_sales = 0
    
    # Generate normal records
    for make in BRANDS:
        # Determine a random chunk of the market
        quantity = random.randint(100, int(total_market_sales / 3))
        accumulated_sales += quantity
        pct = round((quantity / total_market_sales) * 100, 2)
        
        records.append({
            "Year": year,
            "Month": month,
            "Make": make,
            "Quantity": quantity,
            "Pct": pct
        })
    
    # Inject Chaos! (Chaos Engineering for our Fail-Fast Gate)
    if inject_chaos:
        print("[WARNING] Chaos Engineering enabled: Injecting malformed records!")
        records.append({
            "Year": year,
            "Month": month,
            "Make": "", # Missing partition key
            "Quantity": 500,
            "Pct": 5.0
        })
        records.append({
            "Year": year,
            "Month": month,
            "Make": "GhostBrand",
            "Quantity": -150, # Negative quantity
            "Pct": -1.5
        })
        
    # Shuffle so chaos isn't always at the end
    random.shuffle(records)
    
    # Write to CSV
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Year", "Month", "Make", "Quantity", "Pct"])
        writer.writeheader()
        writer.writerows(records)
        
    print(f"[SUCCESS] Mock dataset generated at: {filename}")
    print(f"Total records generated: {len(records)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Mock Norway Car Sales Data")
    parser.add_argument("--chaos", action="store_true", help="Inject malformed data to test Quality Gate")
    args = parser.parse_args()
    
    generate_mock_sales(inject_chaos=args.chaos)
