from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class AnalyticalOrder(BaseModel):
    """
    Data Contract for the Bronze Layer.
    Implements a 'Fail-Fast' quality gate for incoming E-Commerce data.
    Missing primary keys or malformed data will raise ValidationErrors, 
    triggering routing to the Dead Letter / Quarantine bucket.
    """
    customer_id: str = Field(..., description="Unique identifier for the customer.")
    order_id: str = Field(..., description="Unique identifier for the order.")
    order_date: date = Field(..., description="Date of the order, used as SK in DynamoDB and Partition in Iceberg.")
    product_id: str = Field(..., description="Product identifier (StockCode).")
    description: Optional[str] = Field(None, description="Description of the product.")
    quantity: int = Field(..., gt=0, description="Quantity of items, must be greater than zero.")
    unit_price: float = Field(..., ge=0, description="Price per unit, cannot be negative.")
    country: Optional[str] = Field(None, description="Country of the transaction.")

    @field_validator("customer_id", "order_id")
    def validate_not_empty(cls, value: str) -> str:
        """Ensure critical IDs are not valid but empty strings."""
        clean_value = value.strip()
        if not clean_value:
            raise ValueError("Identifier cannot be null or empty.")
        return clean_value


class ApplicationOrder(BaseModel):
    """
    Data Contract for the API (Operational Layer).
    Contains only a subset of the fields required by the frontend/API consumers.
    Optimized for DynamoDB reads.
    """
    customer_id: str = Field(..., description="Partition Key (PK) for DynamoDB.")
    order_date: date = Field(..., description="Sort Key (SK) for DynamoDB.")
    order_id: str = Field(..., description="Unique identifier for the order.")
    total_amount: float = Field(..., description="Total amount for this order line.")
