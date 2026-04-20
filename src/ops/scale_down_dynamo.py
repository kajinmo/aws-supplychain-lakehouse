"""
Lambda: Scale Down DynamoDB to On-Demand Mode.

Called by Step Functions AFTER the Glue batch job finishes.
Switches the operational table back from PROVISIONED to
PAY_PER_REQUEST (On-Demand) to minimize idle costs.

WARNING: AWS only allows switching from Provisioned to On-Demand
ONCE every 24 hours per table. This Lambda should only be invoked
by the daily batch orchestration.
"""
import os
import boto3


def lambda_handler(event: dict, context) -> dict:
    """Switch DynamoDB table back to PAY_PER_REQUEST billing mode."""
    client = boto3.client("dynamodb")
    table_name = os.environ["DYNAMODB_TABLE_NAME"]

    print(f"[ScaleDown] Switching table '{table_name}' to PAY_PER_REQUEST mode...")

    response = client.update_table(
        TableName=table_name,
        BillingMode="PAY_PER_REQUEST",
    )

    new_status = response["TableDescription"]["TableStatus"]
    print(f"[ScaleDown] Table status: {new_status}")

    return {
        "statusCode": 200,
        "action": "SCALE_DOWN",
        "table": table_name,
        "billing_mode": "PAY_PER_REQUEST",
    }
