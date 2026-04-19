import json
import logging
from extract.mock_generator import generate_mock_sales
from extract.ingestion_job import extract_and_validate

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda entry point for the Ingestion Pipeline.
    Triggered by EventBridge with a payload like: {"source": "mock", "chaos": true}
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    source = event.get("source", "mock")
    inject_chaos = event.get("chaos", False)
    
    csv_path = None
    
    if source == "mock":
        logger.info("Running in MOCK mode generator...")
        # Since lambda has an ephemeral /tmp/ directory, we must output there.
        csv_path = generate_mock_sales("/tmp", inject_chaos=inject_chaos)
    else:
        # Future kaggle integration here downloading to /tmp
        logger.warning("Kaggle source not implemented in Serverless yet. Falling back to mock without chaos.")
        csv_path = generate_mock_sales("/tmp", inject_chaos=False)
        
    if not csv_path:
        raise Exception("Failed to generate or download source CSV.")
        
    logger.info("Executing Quality Gate and pushing to S3...")
    
    # We'll adapt ingestion_job to push to S3 using boto3
    result_metrics = extract_and_validate(csv_path)
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Ingestion job completed successfully.",
            "metrics": result_metrics
        })
    }
