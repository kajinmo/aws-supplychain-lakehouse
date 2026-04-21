"""
Lambda: Operational API for Car Sales data.

Serves DynamoDB data through API Gateway HTTP API.
Supports querying by manufacturer (PK) with optional
time filtering via year_month prefix (SK).

Routes:
    GET /sales/{manufacturer}              → All records for a brand
    GET /sales/{manufacturer}?year=2023    → Records for a specific year
    GET /sales                             → List all unique manufacturers
"""
import json
import os
import logging
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB (they break default json.dumps)."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            # Convert to int if it's a whole number, otherwise float
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def lambda_handler(event: dict, context) -> dict:
    """
    API Gateway HTTP API event handler.

    Path parameters and query strings are extracted from the event
    automatically by the HTTP API integration.
    """
    logger.info(f"Event: {json.dumps(event)}")

    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    table = boto3.resource("dynamodb").Table(table_name)

    # Extract route info from HTTP API event format
    route_key = event.get("routeKey", "")
    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    manufacturer = path_params.get("manufacturer")

    # --- Route: GET /sales (List all manufacturers) --- #
    if route_key == "GET /sales" or not manufacturer:
        return _list_manufacturers(table)

    # --- Route: GET /sales/{manufacturer} --- #
    return _query_by_manufacturer(table, manufacturer, query_params)


def _list_manufacturers(table) -> dict:
    """Scan the table and return unique manufacturer names."""
    response = table.scan(
        ProjectionExpression="manufacturer",
    )

    # Extract unique manufacturers from the scan results
    manufacturers = sorted({item["manufacturer"] for item in response["Items"]})

    return _build_response(200, {
        "count": len(manufacturers),
        "manufacturers": manufacturers,
    })


def _query_by_manufacturer(table, manufacturer: str, query_params: dict) -> dict:
    """Query DynamoDB by manufacturer with optional year filter."""
    year_filter = query_params.get("year")

    # Build the KeyConditionExpression dynamically
    if year_filter:
        # Use begins_with on the Sort Key for year prefix queries
        key_condition = (
            Key("manufacturer").eq(manufacturer)
            & Key("year_month").begins_with(year_filter)
        )
    else:
        # Return all records for this manufacturer
        key_condition = Key("manufacturer").eq(manufacturer)

    response = table.query(
        KeyConditionExpression=key_condition,
        ScanIndexForward=True,  # Ascending order by year_month
    )

    items = response.get("Items", [])

    if not items:
        return _build_response(404, {
            "error": f"No sales data found for manufacturer: {manufacturer}",
        })

    return _build_response(200, {
        "manufacturer": manufacturer,
        "count": len(items),
        "sales": items,
    })


def _build_response(status_code: int, body: dict) -> dict:
    """Standard API Gateway HTTP API response format."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # CORS for Streamlit frontend
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }
