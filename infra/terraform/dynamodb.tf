resource "aws_dynamodb_table" "operational" {
  name         = "${var.project_name}-operational"
  billing_mode = "PAY_PER_REQUEST" # Crucial to stay in Free Tier initially
  hash_key     = "manufacturer"
  range_key    = "year_month"

  attribute {
    name = "manufacturer"
    type = "S"
  }

  attribute {
    name = "year_month"
    type = "S"
  }

  # Point-in-time recovery is a best practice, but usually charges after free tier.
  # We leave it disabled intentionally for a strict free-tier setup, or enable it if explicit protection is needed.
  point_in_time_recovery {
    enabled = false
  }

  tags = {
    Name = "${var.project_name}-operational"
  }
}
