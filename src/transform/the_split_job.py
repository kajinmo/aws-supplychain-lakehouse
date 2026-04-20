import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

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
# Onde nossos dados moram
bronze_path = f"s3://{args['BRONZE_BUCKET_NAME']}/"

print(f"Lendo dados Parquet do bucket Bronze: {bronze_path}")

# Lemos a pasta inteira de uma vez. O Spark é inteligente o bastante
# para ler todos os arquivos .parquet dentro de subpastas em paralelo.
df_bronze = spark.read.parquet(bronze_path)

# ==========================================
# ROTA 1: ESCALA ANALÍTICA COM APACHE ICEBERG
# ==========================================
print("Iniciando gravação na Rota 1 (Apache Iceberg)...")

# Fazemos o cache aqui! O `.show()` da linha seguinte ativará esse cache.
df_bronze.cache()

# Mostra as primeiras 5 linhas no terminal (para nosso debug futuro no CloudWatch)
df_bronze.show(5)

db_name = "lakehouse_db"
table_name = "norway_car_sales_silver"
iceberg_path = f"s3://{args['SILVER_BUCKET_NAME']}/iceberg/{table_name}/"

# Aqui a mágica do Iceberg acontece (DataFrameWriterV2)
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

# 1. Transformação do cluster em formato amigável para AWS
dyf_bronze = DynamicFrame.fromDF(df_bronze, glueContext, "dyf_bronze")

# 2. O verdadeiro segredo da Engenharia Sênior aqui: dynamodb.throughput.write.percent
# Definido em 0.5 (50%), informa aos Workers do Glue para se cadenciarem e jamais
# esgotarem as humíldes Write Capacity Units (WCU) do nosso modelo Free Tier.
glueContext.write_dynamic_frame.from_options(
    frame=dyf_bronze,
    connection_type="dynamodb",
    connection_options={
        "dynamodb.output.tableName": args['DYNAMODB_TABLE_NAME'],
        "dynamodb.throughput.write.percent": "0.5" 
    }
)

print("Rota 2 (DynamoDB) concluída com sucesso!")

job.commit()
