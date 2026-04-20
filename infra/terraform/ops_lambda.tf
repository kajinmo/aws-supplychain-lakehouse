# ==========================================
# Lambdas Operacionais: DynamoDB Scaling
# ==========================================

# --- ZIP Packaging --- #
data "archive_file" "scale_up_zip" {
  type        = "zip"
  source_file = "${path.module}/../../src/ops/scale_up_dynamo.py"
  output_path = "${path.module}/../../scale_up_deployment.zip"
}

data "archive_file" "scale_down_zip" {
  type        = "zip"
  source_file = "${path.module}/../../src/ops/scale_down_dynamo.py"
  output_path = "${path.module}/../../scale_down_deployment.zip"
}

# --- IAM: DynamoDB Scaling Role --- #
data "aws_iam_policy_document" "dynamo_scaling_policy" {
  statement {
    actions = [
      "dynamodb:UpdateTable",
      "dynamodb:DescribeTable"
    ]
    resources = [aws_dynamodb_table.operational.arn]
  }
}

resource "aws_iam_policy" "dynamo_scaling" {
  name        = "${var.project_name}-dynamo-scaling-policy"
  description = "Allow Lambda to switch DynamoDB billing modes"
  policy      = data.aws_iam_policy_document.dynamo_scaling_policy.json
}

resource "aws_iam_role" "ops_lambda_role" {
  name               = "${var.project_name}-ops-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "ops_lambda_basic" {
  role       = aws_iam_role.ops_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "ops_lambda_dynamo" {
  role       = aws_iam_role.ops_lambda_role.name
  policy_arn = aws_iam_policy.dynamo_scaling.arn
}

# --- Lambda Functions --- #
resource "aws_lambda_function" "scale_up_dynamo" {
  function_name    = "${var.project_name}-scale-up-dynamo"
  role             = aws_iam_role.ops_lambda_role.arn
  handler          = "scale_up_dynamo.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.scale_up_zip.output_path
  source_code_hash = data.archive_file.scale_up_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.operational.name
    }
  }
}

resource "aws_lambda_function" "scale_down_dynamo" {
  function_name    = "${var.project_name}-scale-down-dynamo"
  role             = aws_iam_role.ops_lambda_role.arn
  handler          = "scale_down_dynamo.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  filename         = data.archive_file.scale_down_zip.output_path
  source_code_hash = data.archive_file.scale_down_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.operational.name
    }
  }
}
