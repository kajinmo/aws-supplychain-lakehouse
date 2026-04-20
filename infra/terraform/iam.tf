data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ingestion_lambda_role" {
  name               = "${var.project_name}-ingestion-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

# Attach basic execution role for CloudWatch logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.ingestion_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Add policy for pushing to S3 Bronze and Quarantine
data "aws_iam_policy_document" "lambda_s3_push" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl"
    ]
    resources = [
      "${aws_s3_bucket.bronze.arn}/*",
      "${aws_s3_bucket.quarantine.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "lambda_s3_access" {
  name        = "${var.project_name}-s3-push-policy"
  description = "Allow ingestion lambda to push objects to Bronze and Quarantine buckets"
  policy      = data.aws_iam_policy_document.lambda_s3_push.json
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
  role       = aws_iam_role.ingestion_lambda_role.name
  policy_arn = aws_iam_policy.lambda_s3_access.arn
}

# ==========================================
# IAM: AWS Glue "The Split" Job
# ==========================================
data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue_split_job_role" {
  name               = "${var.project_name}-glue-split-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
}

# 1. AWS Managed Policy for Glue (Basic execution & logging)
resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue_split_job_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# 2. Custom Policy for Free Tier Resource Access (S3 & DynamoDB)
data "aws_iam_policy_document" "glue_resource_access" {
  # Read from Bronze
  statement {
    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.bronze.arn,
      "${aws_s3_bucket.bronze.arn}/*"
    ]
  }

  # Write to Silver (Iceberg) and Scripts
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.silver.arn,
      "${aws_s3_bucket.silver.arn}/*"
    ]
  }

  # Write to DynamoDB
  statement {
    actions = [
      "dynamodb:PutItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:DescribeTable"
    ]
    resources = [
      aws_dynamodb_table.operational.arn
    ]
  }
}

resource "aws_iam_policy" "glue_resource_policy" {
  name        = "${var.project_name}-glue-resources-policy"
  description = "Allows Glue job to access S3 Bronze, Silver, and DynamoDB"
  policy      = data.aws_iam_policy_document.glue_resource_access.json
}

resource "aws_iam_role_policy_attachment" "glue_resource_attach" {
  role       = aws_iam_role.glue_split_job_role.name
  policy_arn = aws_iam_policy.glue_resource_policy.arn
}
