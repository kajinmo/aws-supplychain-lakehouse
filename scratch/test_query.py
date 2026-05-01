import os
import sys
sys.path.append(os.path.abspath("frontend"))
from services.athena_client import AthenaClient

def test_queries(year):
    athena = AthenaClient()
    print(f"\n--- Testing Year {year} ---")
    
    try:
        print("1. gold_market_leaders...")
        res1 = athena.run_gold_query(f"SELECT * FROM gold_market_leaders WHERE year = {year} LIMIT 10")
        print(f"SUCCESS. Rows: {len(res1)}")
    except Exception as e:
        print(f"FAILED: {e}")

    try:
        print("2. gold_brand_concentration...")
        res2 = athena.run_gold_query("SELECT * FROM gold_brand_concentration ORDER BY year ASC")
        print(f"SUCCESS. Rows: {len(res2)}")
    except Exception as e:
        print(f"FAILED: {e}")

    try:
        print("3. gold_yoy_growth...")
        res3 = athena.get_yoy_growth(year)
        print(f"SUCCESS. Rows: {len(res3)}")
    except Exception as e:
        print(f"FAILED: {e}")

    try:
        print("4. gold_emerging_brands...")
        res4 = athena.run_gold_query(f"SELECT * FROM gold_emerging_brands WHERE year = {year} ORDER BY total_units DESC LIMIT 8")
        print(f"SUCCESS. Rows: {len(res4)}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_queries(2007)
    test_queries(2008)
