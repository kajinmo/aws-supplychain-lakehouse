from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CarSalesAnalytical(BaseModel):
    """
    Data Contract for the Bronze Layer (Norway Car Sales).
    Enforces strict typing and presence of primary keys.
    """
    year: int = Field(..., alias="Year", description="Year of sales.")
    month: int = Field(..., alias="Month", description="Month of sales.")
    make: str = Field(..., alias="Make", description="Manufacturer name.")
    quantity: int = Field(..., alias="Quantity", ge=0, description="Total units sold.")
    pct: float = Field(..., alias="Pct", description="Market share percentage.")

    @field_validator("make")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        """Ensure the manufacturer name is not an empty string."""
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("Manufacturer name cannot be empty.")
        return clean_value


class CarSalesApplication(BaseModel):
    """
    Data Contract for the API (Operational Layer).
    Using 'manufacturer' instead of 'make' as per user requirement.
    Optimized for DynamoDB reads with a composite Sort Key (year_month).
    """
    manufacturer: str = Field(..., description="Partition Key (PK). Manufacturer name.")
    year_month: str = Field(..., description="Sort Key (SK). Format: YYYY-MM.")
    quantity: int = Field(..., description="Total units sold in the period.")
    market_share_pct: float = Field(..., description="Percentage of market share.")
