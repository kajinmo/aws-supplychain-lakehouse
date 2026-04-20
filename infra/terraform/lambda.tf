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

# ==========================================
# EventBridge Scheduler (Modern): Hourly Mock Ingestion
# ==========================================

# IAM: Allow Scheduler to invoke the ingestion Lambda
data "aws_iam_policy_document" "scheduler_lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "scheduler_lambda_policy" {
  statement {
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.ingestion_lambda.arn]
  }
}

resource "aws_iam_role" "scheduler_lambda_role" {
  name               = "${var.project_name}-scheduler-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_lambda_assume.json
}

resource "aws_iam_policy" "scheduler_lambda" {
  name   = "${var.project_name}-scheduler-lambda-policy"
  policy = data.aws_iam_policy_document.scheduler_lambda_policy.json
}

resource "aws_iam_role_policy_attachment" "scheduler_lambda_attach" {
  role       = aws_iam_role.scheduler_lambda_role.name
  policy_arn = aws_iam_policy.scheduler_lambda.arn
}

# Fires every hour, injecting mock chaos payload into the Lambda
resource "aws_scheduler_schedule" "hourly_ingestion" {
  name       = "${var.project_name}-hourly-ingestion"
  group_name = "default"

  schedule_expression          = "rate(1 hour)"
  schedule_expression_timezone = "America/Sao_Paulo"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.ingestion_lambda.arn
    role_arn = aws_iam_role.scheduler_lambda_role.arn

    # Inject the same mock payload our Lambda expects
    input = jsonencode({
      source = "mock"
      chaos  = true
    })

    retry_policy {
      maximum_retry_attempts       = 1
      maximum_event_age_in_seconds = 1800 # Discard stale ingestion after 30 min
    }
  }
}
