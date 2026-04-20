resource "aws_dynamodb_table" "operational" {
  name         = "${var.project_name}-operational"
  billing_mode = "PAY_PER_REQUEST"
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

  point_in_time_recovery {
    enabled = false
  }

  tags = {
    Name = "${var.project_name}-operational"
  }
}
