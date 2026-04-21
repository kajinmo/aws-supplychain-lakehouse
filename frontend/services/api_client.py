import requests
import pandas as pd
from .config import API_BASE_URL

class APIClient:
    """Service to interact with the Operational API (API Gateway/DynamoDB)."""

    @staticmethod
    def get_all_manufacturers():
        """Fetch the list of unique manufacturers."""
        try:
            response = requests.get(f"{API_BASE_URL}/sales", timeout=10)
            response.raise_for_status()
            data = response.json()
            return sorted(data.get("manufacturers", []))
        except Exception as e:
            print(f"Error fetching manufacturers: {e}")
            return []

    @staticmethod
    def get_sales_by_brand(brand: str, year: int = None):
        """
        Fetch sales data for a specific brand from the operational API.
        
        Args:
            brand: The manufacturer name (e.g., 'Tesla')
            year: Optional filter for a specific year
        """
        try:
            url = f"{API_BASE_URL}/sales/{brand}"
            params = {"year": year} if year else {}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("sales"):
                return pd.DataFrame()
            
            df = pd.DataFrame(data["sales"])
            
            # Sort by year_month for consistent charts
            if "year_month" in df.columns:
                df = df.sort_values("year_month")
                
            return df
        except Exception as e:
            print(f"Error fetching sales for {brand}: {e}")
            return pd.DataFrame()
