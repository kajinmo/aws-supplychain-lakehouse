"""
Lambda: Scale Up DynamoDB to Provisioned Mode.

Called by Step Functions BEFORE the Glue batch job starts.
Switches the operational table from PAY_PER_REQUEST (On-Demand) to
PROVISIONED mode with Free Tier capacity limits (25 WCU / 25 RCU).
"""
import os
import boto3


def lambda_handler(event: dict, context) -> dict:
    """Switch DynamoDB table to PROVISIONED billing mode."""
    client = boto3.client("dynamodb")
    table_name = os.environ["DYNAMODB_TABLE_NAME"]

    print(f"[ScaleUp] Switching table '{table_name}' to PROVISIONED mode...")

    response = client.update_table(
        TableName=table_name,
        BillingMode="PROVISIONED",
        ProvisionedThroughput={
            "ReadCapacityUnits": 25,   # Free Tier limit
            "WriteCapacityUnits": 25,  # Free Tier limit
        },
    )

    new_status = response["TableDescription"]["TableStatus"]
    print(f"[ScaleUp] Table status: {new_status}")

    return {
        "statusCode": 200,
        "action": "SCALE_UP",
        "table": table_name,
        "billing_mode": "PROVISIONED",
        "wcu": 25,
        "rcu": 25,
    }
