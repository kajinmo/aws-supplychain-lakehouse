# ==========================================
# S3: Upload do Script PySpark
# ==========================================
resource "aws_s3_object" "glue_script" {
  bucket = aws_s3_bucket.silver.id
  key    = "scripts/the_split_job.py"
  source = "${path.module}/../../src/transform/the_split_job.py"
  etag   = filemd5("${path.module}/../../src/transform/the_split_job.py")
}

# ==========================================
# AWS Glue Catalog (O Banco do Athena)
# ==========================================
resource "aws_glue_catalog_database" "lakehouse_db" {
  name        = "lakehouse_db"
  description = "Database for Norway Car Sales Lakehouse (Silver Layer)"
}

# ==========================================
# AWS Glue Job (The Split)
# ==========================================
resource "aws_glue_job" "the_split" {
  name     = "${var.project_name}-the-split-job"
  role_arn = aws_iam_role.glue_split_job_role.arn

  description = "PySpark Job to split Bronze parquets into Iceberg (Silver) and DynamoDB (Operational)"

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.silver.id}/${aws_s3_object.glue_script.key}"
    python_version  = "3"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  # FREE TIER GUARDSLIPS
  worker_type       = "G.1X" # Padrão mais barato (4 vCPUs, 16 GB memory)
  number_of_workers = 2      # Mínimo absoluto permitido pelo AWS Glue
  timeout           = 15     # Timeout estrito em 15 minutos (evitar cobrança absurda por esquecimento)
  max_retries       = 0      # Fail fast, não re-tentar automaticamente consumindo o orçamento

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-metrics"                   = "true" # Essencial para vermos se estamos limitando o Dynamo
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${aws_s3_bucket.silver.id}/spark-history-logs/"

    # Suporte ao formato Apache Iceberg native no Glue
    "--datalake-formats" = "iceberg"
    "--conf"             = "spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions --conf spark.sql.catalog.glue_catalog=org.apache.iceberg.spark.SparkCatalog --conf spark.sql.catalog.glue_catalog.warehouse=s3://${aws_s3_bucket.silver.id}/iceberg/ --conf spark.sql.catalog.glue_catalog.catalog-impl=org.apache.iceberg.aws.glue.GlueCatalog --conf spark.sql.catalog.glue_catalog.io-impl=org.apache.iceberg.aws.s3.S3FileIO"

    # Injeção das variáveis consumidas pelo nosso args = getResolvedOptions() no Python
    "--BRONZE_BUCKET_NAME"  = aws_s3_bucket.bronze.id
    "--SILVER_BUCKET_NAME"  = aws_s3_bucket.silver.id
    "--DYNAMODB_TABLE_NAME" = aws_dynamodb_table.operational.name
  }
}
