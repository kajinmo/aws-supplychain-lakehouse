# ==========================================
# EventBridge Scheduler (Modern): Batch Orchestration
# ==========================================

# --- IAM for Scheduler to invoke Step Functions --- #
data "aws_iam_policy_document" "scheduler_sfn_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "scheduler_sfn_policy" {
  statement {
    actions   = ["states:StartExecution"]
    resources = [aws_sfn_state_machine.batch_orchestrator.arn]
  }
}

resource "aws_iam_role" "scheduler_sfn_role" {
  name               = "${var.project_name}-scheduler-sfn-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_sfn_assume.json
}

resource "aws_iam_policy" "scheduler_sfn" {
  name   = "${var.project_name}-scheduler-sfn-policy"
  policy = data.aws_iam_policy_document.scheduler_sfn_policy.json
}

resource "aws_iam_role_policy_attachment" "scheduler_sfn_attach" {
  role       = aws_iam_role.scheduler_sfn_role.name
  policy_arn = aws_iam_policy.scheduler_sfn.arn
}

# --- Daily Batch: 19:00 BRT (native timezone, no UTC math needed) --- #
resource "aws_scheduler_schedule" "daily_batch" {
  name       = "${var.project_name}-daily-batch"
  group_name = "default"

  schedule_expression          = "cron(0 19 * * ? *)"
  schedule_expression_timezone = "America/Sao_Paulo" # AWS handles DST automatically

  flexible_time_window {
    mode = "OFF" # Fire exactly at 19:00, no flex window
  }

  target {
    arn      = aws_sfn_state_machine.batch_orchestrator.arn
    role_arn = aws_iam_role.scheduler_sfn_role.arn

    # What to do if the trigger fails (e.g., Step Functions is unavailable)
    retry_policy {
      maximum_retry_attempts       = 2
      maximum_event_age_in_seconds = 3600 # Give up after 1h to avoid stale runs
    }
  }
}
