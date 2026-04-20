# ==========================================
# AWS Step Functions: Batch Orchestration
# ==========================================

# --- IAM for Step Functions --- #
data "aws_iam_policy_document" "sfn_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "sfn_execution_policy" {
  # Invoke Lambdas
  statement {
    actions = ["lambda:InvokeFunction"]
    resources = [
      aws_lambda_function.scale_up_dynamo.arn,
      aws_lambda_function.scale_down_dynamo.arn
    ]
  }

  # Start and monitor Glue Job
  statement {
    actions = [
      "glue:StartJobRun",
      "glue:GetJobRun",
      "glue:GetJobRuns",
      "glue:BatchStopJobRun"
    ]
    resources = [aws_glue_job.the_split.arn]
  }
}

resource "aws_iam_role" "sfn_role" {
  name               = "${var.project_name}-sfn-role"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume_role.json
}

resource "aws_iam_policy" "sfn_execution" {
  name        = "${var.project_name}-sfn-execution-policy"
  description = "Allow Step Functions to invoke Lambdas and run Glue Jobs"
  policy      = data.aws_iam_policy_document.sfn_execution_policy.json
}

resource "aws_iam_role_policy_attachment" "sfn_execution_attach" {
  role       = aws_iam_role.sfn_role.name
  policy_arn = aws_iam_policy.sfn_execution.arn
}

# --- State Machine Definition --- #
resource "aws_sfn_state_machine" "batch_orchestrator" {
  name     = "${var.project_name}-batch-orchestrator"
  role_arn = aws_iam_role.sfn_role.arn

  definition = jsonencode({
    Comment = "Daily batch: Scale DynamoDB -> Run Glue -> Scale Down"
    StartAt = "ScaleUpDynamoDB"
    States = {
      ScaleUpDynamoDB = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.scale_up_dynamo.arn
          Payload      = { "source" = "step-functions" }
        }
        ResultPath = "$.scaleUpResult"
        Next       = "WaitForTableUpdate"
      }

      WaitForTableUpdate = {
        Type    = "Wait"
        Seconds = 30
        Comment = "Allow DynamoDB time to switch billing mode"
        Next    = "RunGlueJob"
      }

      RunGlueJob = {
        Type     = "Task"
        Resource = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = {
          JobName = aws_glue_job.the_split.name
        }
        ResultPath = "$.glueResult"
        Next       = "ScaleDownDynamoDB"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "ScaleDownDynamoDB"
          ResultPath  = "$.glueError"
          Comment     = "Even if Glue fails, always scale down to save costs"
        }]
      }

      ScaleDownDynamoDB = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = aws_lambda_function.scale_down_dynamo.arn
          Payload      = { "source" = "step-functions" }
        }
        ResultPath = "$.scaleDownResult"
        End        = true
      }
    }
  })
}
