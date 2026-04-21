import boto3
from datetime import datetime
from .config import AWS_REGION, SFN_NAME, GLUE_JOB_NAME

class AWSMetadata:
    """Service to fetch AWS infrastructure status (Step Functions, Glue)."""

    def __init__(self):
        self.sfn = boto3.client("stepfunctions", region_name=AWS_REGION)
        self.glue = boto3.client("glue", region_name=AWS_REGION)

    def get_pipeline_status(self):
        """Fetch status of the latest Step Functions executions."""
        try:
            # Get SFN ARN first
            state_machines = self.sfn.list_state_machines()
            sfn_arn = next(
                (sm["stateMachineArn"] for sm in state_machines["stateMachines"] if SFN_NAME in sm["name"]),
                None
            )

            if not sfn_arn:
                return []

            executions = self.sfn.list_executions(
                stateMachineArn=sfn_arn,
                maxResults=5
            )

            results = []
            for ex in executions["executions"]:
                results.append({
                    "name": ex["name"],
                    "status": ex["status"],
                    "started": ex["startDate"].strftime("%Y-%m-%d %H:%M"),
                    "stopDate": ex.get("stopDate", datetime.now()).strftime("%Y-%m-%d %H:%M")
                })
            return results
        except Exception:
            return []

    def get_glue_job_metrics(self):
        """Fetch metrics from the latest Glue Job run."""
        try:
            runs = self.glue.get_job_runs(JobName=GLUE_JOB_NAME, MaxResults=1)
            if not runs["JobRuns"]:
                return None
            
            latest = runs["JobRuns"][0]
            return {
                "id": latest["Id"],
                "status": latest["JobRunState"],
                "duration": latest.get("ExecutionTime", 0),
                "started": latest["StartedOn"].strftime("%Y-%m-%d %H:%M")
            }
        except Exception:
            return None
