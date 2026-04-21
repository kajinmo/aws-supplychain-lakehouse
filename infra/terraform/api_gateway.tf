# ==========================================
# Operational API: Lambda + API Gateway HTTP API
# ==========================================

# --- ZIP Packaging --- #
data "archive_file" "operational_api_zip" {
  type        = "zip"
  source_file = "${path.module}/../../src/api/operational_api.py"
  output_path = "${path.module}/../../operational_api_deployment.zip"
}

# --- IAM: API Lambda Role --- #
data "aws_iam_policy_document" "api_lambda_dynamo_read" {
  statement {
    actions = [
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:GetItem"
    ]
    resources = [aws_dynamodb_table.operational.arn]
  }
}

resource "aws_iam_role" "api_lambda_role" {
  name               = "${var.project_name}-api-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  role       = aws_iam_role.api_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "api_lambda_dynamo" {
  name        = "${var.project_name}-api-dynamo-read-policy"
  description = "Allow API Lambda to read from DynamoDB operational table"
  policy      = data.aws_iam_policy_document.api_lambda_dynamo_read.json
}

resource "aws_iam_role_policy_attachment" "api_lambda_dynamo_attach" {
  role       = aws_iam_role.api_lambda_role.name
  policy_arn = aws_iam_policy.api_lambda_dynamo.arn
}

# --- Lambda Function --- #
resource "aws_lambda_function" "operational_api" {
  function_name    = "${var.project_name}-operational-api"
  role             = aws_iam_role.api_lambda_role.arn
  handler          = "operational_api.lambda_handler"
  runtime          = "python3.12"
  timeout          = 10
  memory_size      = 128 # Read-only API, minimal memory needed
  filename         = data.archive_file.operational_api_zip.output_path
  source_code_hash = data.archive_file.operational_api_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.operational.name
    }
  }
}

# ==========================================
# API Gateway HTTP API (v2 - Modern, cheaper)
# ==========================================
resource "aws_apigatewayv2_api" "sales_api" {
  name          = "${var.project_name}-sales-api"
  protocol_type = "HTTP"
  description   = "Public HTTP API for operational car sales data"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "OPTIONS"]
    allow_headers = ["Content-Type"]
    max_age       = 3600
  }
}

# Auto-deploy stage (no manual deployment needed)
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.sales_api.id
  name        = "$default"
  auto_deploy = true
}

# Lambda integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.sales_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.operational_api.invoke_arn
  payload_format_version = "2.0"
}

# Route: GET /sales (list all manufacturers)
resource "aws_apigatewayv2_route" "list_sales" {
  api_id    = aws_apigatewayv2_api.sales_api.id
  route_key = "GET /sales"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Route: GET /sales/{manufacturer} (query by brand)
resource "aws_apigatewayv2_route" "get_sales_by_manufacturer" {
  api_id    = aws_apigatewayv2_api.sales_api.id
  route_key = "GET /sales/{manufacturer}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Allow API Gateway to invoke our Lambda
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.operational_api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.sales_api.execution_arn}/*/*"
}

# --- Output the API URL for easy access --- #
output "api_endpoint" {
  description = "Public URL for the Sales API"
  value       = aws_apigatewayv2_api.sales_api.api_endpoint
}
