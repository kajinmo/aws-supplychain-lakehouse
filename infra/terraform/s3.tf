# Local variable to generate a random or account-specific suffix to avoid S3 bucket name collisions
data "aws_caller_identity" "current" {}

locals {
  bucket_suffix = data.aws_caller_identity.current.account_id
}

# Bronze: Raw Ingested Data (Fail-Fast Passed)
resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-bronze-${local.bucket_suffix}"

  # Safe guard: Prevents accidental destruction of data without explicit override
  force_destroy = false
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze_encryption" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Silver: Apache Iceberg Tables (Analytical)
resource "aws_s3_bucket" "silver" {
  bucket        = "${var.project_name}-silver-${local.bucket_suffix}"
  force_destroy = false
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver_encryption" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Quarantine: Dead Letter / Malformed records (Failed Validation)
resource "aws_s3_bucket" "quarantine" {
  bucket        = "${var.project_name}-quar-${local.bucket_suffix}"
  force_destroy = false
}

resource "aws_s3_bucket_lifecycle_configuration" "quarantine_lifecycle" {
  bucket = aws_s3_bucket.quarantine.id

  rule {
    id     = "expire_quarantine_records"
    status = "Enabled"

    filter {} # Required by provider 5.x

    expiration {
      days = 30 # Delete malformed records after 30 days to save costs
    }
  }
}

# Athena Results: Temporary storage for SQL query results
resource "aws_s3_bucket" "athena_results" {
  bucket        = "${var.project_name}-athena-results-${local.bucket_suffix}"
  force_destroy = true # Safe to delete results as they are temporary
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results_lifecycle" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "expire_results_after_1_day"
    status = "Enabled"

    filter {}

    expiration {
      days = 1 # Keep environment clean and avoid storage costs
    }
  }
}
