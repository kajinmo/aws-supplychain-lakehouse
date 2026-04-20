resource "aws_lambda_function" "ingestion_lambda" {
  function_name = "${var.project_name}-ingestion-job"
  role          = aws_iam_role.ingestion_lambda_role.arn
  handler       = "api.lambda_handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 300 # 5 minutes timeout
  memory_size   = 256 # Higher memory to process pandas properly

  filename         = "../../lambda_deployment.zip"
  source_code_hash = filebase64sha256("../../lambda_deployment.zip")

  # Attach AWS SDK for pandas (AWS DataWrangler) to avoid packaging massive wheels
  layers = [
    "arn:aws:lambda:${var.aws_region}:336392948345:layer:AWSSDKPandas-Python312:14"
  ]

  environment {
    variables = {
      BRONZE_BUCKET     = aws_s3_bucket.bronze.bucket
      QUARANTINE_BUCKET = aws_s3_bucket.quarantine.bucket
    }
  }

  tags = {
    Name = "${var.project_name}-ingestion-lambda"
  }
}

# --- EventBridge Scheduler --- #
resource "aws_cloudwatch_event_rule" "hourly_ingestion" {
  name                = "${var.project_name}-hourly-ingestion"
  description         = "Triggers mock ingestion every hour to simulate continuous data arrival"
  schedule_expression = "rate(1 hour)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.hourly_ingestion.name
  target_id = "TriggerLambda"
  arn       = aws_lambda_function.ingestion_lambda.arn

  # Inject the payload specific for our mock generator
  input = jsonencode({
    "source" : "mock",
    "chaos" : true
  })
}

resource "aws_lambda_permission" "allow_eventbridge_to_invoke_lambda" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_ingestion.arn
}
