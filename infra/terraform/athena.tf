# ==========================================
# Athena Workgroup: Automatiza a configuração de resultados
# ==========================================
resource "aws_athena_workgroup" "lakehouse_workgroup" {
  name = "${var.project_name}-workgroup"

  configuration {
    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    # Forçar o uso desta configuração para todos os usuários deste workgroup
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true
  }

  force_destroy = true
}
