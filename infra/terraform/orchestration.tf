# ==========================================
# EventBridge: Batch Orchestration Schedule
# ==========================================

# Trigger Step Functions daily at 19:00 BRT (22:00 UTC)
resource "aws_cloudwatch_event_rule" "daily_batch" {
  name                = "${var.project_name}-daily-batch"
  description         = "Triggers the batch orchestrator (Step Functions) at 19:00 BRT daily"
  schedule_expression = "cron(0 22 * * ? *)"
}

# IAM for EventBridge to invoke Step Functions
data "aws_iam_policy_document" "eventbridge_sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "eventbridge_sfn_policy" {
  statement {
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.batch_orchestrator.arn]
  }
}

resource "aws_iam_role" "eventbridge_sfn_role" {
  name               = "${var.project_name}-eb-sfn-role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_sfn_assume.json
}

resource "aws_iam_policy" "eventbridge_sfn" {
  name   = "${var.project_name}-eb-sfn-policy"
  policy = data.aws_iam_policy_document.eventbridge_sfn_policy.json
}

resource "aws_iam_role_policy_attachment" "eventbridge_sfn_attach" {
  role       = aws_iam_role.eventbridge_sfn_role.name
  policy_arn = aws_iam_policy.eventbridge_sfn.arn
}

resource "aws_cloudwatch_event_target" "sfn_target" {
  rule     = aws_cloudwatch_event_rule.daily_batch.name
  arn      = aws_sfn_state_machine.batch_orchestrator.arn
  role_arn = aws_iam_role.eventbridge_sfn_role.arn
}
