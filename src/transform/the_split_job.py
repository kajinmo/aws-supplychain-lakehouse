import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as f

# 1. Captura de Parâmetros Injetados pelo Terraform
args = getResolvedOptions(sys.argv, [
    'JOB_NAME', 
    'BRONZE_BUCKET_NAME', 
    'SILVER_BUCKET_NAME', 
    'DYNAMODB_TABLE_NAME'
])

# 2. Inicialização do "Motor" do Apache Spark na AWS
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# ==========================================
# FASE 1: LEITURA DOS DADOS (BRONZE)
# ==========================================
bronze_path = f"s3://{args['BRONZE_BUCKET_NAME']}/"

print(f"Lendo dados Parquet do bucket Bronze: {bronze_path}")

df_bronze = spark.read.parquet(bronze_path)
df_bronze.cache()
df_bronze.printSchema()

# ==========================================
# ROTA 1: ESCALA ANALÍTICA COM APACHE ICEBERG
# ==========================================
print("Iniciando gravação na Rota 1 (Apache Iceberg)...")

db_name = "lakehouse_db"
table_name = "norway_car_sales_silver"
iceberg_path = f"s3://{args['SILVER_BUCKET_NAME']}/iceberg/{table_name}/"

# Registramos os dados no bucket Silver E no Glue Data Catalog (Athena) simultaneamente.
(df_bronze.writeTo(f"glue_catalog.{db_name}.{table_name}")
    .tableProperty("location", iceberg_path)
    .tableProperty("format-version", "2")  # v2 habilita manutenções eficientes (Row-level deletes, Merge-on-Read)
    .partitionedBy("year")
    .createOrReplace())

print("Rota 1 (Iceberg) concluída com sucesso!")

# ==========================================
# ROTA 2: OPERACIONAL (DYNAMODB)
# ==========================================
print(f"Iniciando gravação na Rota 2 (DynamoDB) na tabela: {args['DYNAMODB_TABLE_NAME']} ...")

# 1. Mapeamento de Dados (Data Mapping)
# Transformamos o schema do Bronze para o schema exigido pelo DynamoDB (PK/SK)
df_operational = df_bronze \
    .withColumn("manufacturer", f.col("Make")) \
    .withColumn("year_month", f.concat(
        f.col("Year"), 
        f.lit("-"), 
        f.lpad(f.col("Month"), 2, "0")
    )) \
    .select("manufacturer", "year_month", "Quantity", "Pct")

# 2. Transformação para formato AWS DynamicFrame
dyf_operational = DynamicFrame.fromDF(df_operational, glueContext, "dyf_operational")

# 3. Gravação controlada com limitador de throughput 
glueContext.write_dynamic_frame.from_options(
    frame=dyf_operational,
    connection_type="dynamodb",
    connection_options={
        "dynamodb.output.tableName": args['DYNAMODB_TABLE_NAME'],
        "dynamodb.throughput.write.percent": "0.5" 
    }
)

print("Rota 2 (DynamoDB) concluída com sucesso!")

job.commit()
