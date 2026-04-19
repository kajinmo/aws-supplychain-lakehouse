# This bucket will store the Terraform state.
# We will use the S3 native Conditional Writes (use_lockfile = true) for locking, available in Terraform 1.10+
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.project_name}-tfstate-${local.bucket_suffix}"

  # Safe guard: Prevents accidental destruction of state.
  force_destroy = false
}

resource "aws_s3_bucket_versioning" "terraform_state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state_encryption" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
