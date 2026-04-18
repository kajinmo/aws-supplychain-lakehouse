variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project to tag resources"
  type        = string
  default     = "car-sales-lakehouse"
}

variable "budget_alert_email" {
  description = "Email address for AWS Cost Alerts"
  type        = string
  # No default, should be provided via TF_VAR_budget_alert_email from .env
}
