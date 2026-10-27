import sys

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions

from pyspark.context import SparkContext
from pyspark.sql.functions import (
    col,
    current_timestamp,
    dayofmonth,
    input_file_name,
    month,
    to_date,
    trim,
    upper,
    year,
)


# ============================================================
# PARAMETROS
# ============================================================

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "RAW_BUCKET",
        "BRONZE_BUCKET",
        "SILVER_BUCKET"
    ]
)

RAW_BUCKET = args["RAW_BUCKET"]
BRONZE_BUCKET = args["BRONZE_BUCKET"]
SILVER_BUCKET = args["SILVER_BUCKET"]


# ============================================================
# CONTEXTO GLUE
# ============================================================

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


# ============================================================
# CAMINHOS
# ============================================================

input_path = (
    f"s3://{RAW_BUCKET}/vendas/historico/"
)

bronze_path = (
    f"s3://{BRONZE_BUCKET}/vendas/"
)

silver_path = (
    f"s3://{SILVER_BUCKET}/vendas/"
)


print("========================================")
print("TECHNOVA | GLUE ETL")
print("========================================")
print(f"RAW: {input_path}")
print(f"BRONZE: {bronze_path}")
print(f"SILVER: {silver_path}")


# ============================================================
# LEITURA DA CAMADA RAW
# ============================================================

df_raw = (
    spark.read
    .option("header", "true")
    .option("recursiveFileLookup", "true")
    .csv(input_path)
)


raw_count = df_raw.count()

print()
print(f"Registros RAW: {raw_count}")


# ============================================================
# BRONZE
#
# Transformacoes tecnicas:
# - tipagem
# - rastreabilidade
# - particionamento
# - conversao para Parquet
# ============================================================

df_bronze = (
    df_raw

    .withColumn(
        "order_id",
        col("order_id").cast("long")
    )

    .withColumn(
        "quantity",
        col("quantity").cast("integer")
    )

    .withColumn(
        "unit_price",
        col("unit_price").cast("decimal(12,2)")
    )

    .withColumn(
        "price_rs",
        col("price_rs").cast("decimal(12,2)")
    )

    .withColumn(
        "discount_pct",
        col("discount_pct").cast("integer")
    )

    .withColumn(
        "final_price_rs",
        col("final_price_rs").cast("decimal(12,2)")
    )

    .withColumn(
        "shipping_cost",
        col("shipping_cost").cast("decimal(12,2)")
    )

    .withColumn(
        "delivery_days",
        col("delivery_days").cast("integer")
    )

    .withColumn(
        "purchase_date",
        to_date(
            col("purchase_date"),
            "yyyy-MM-dd"
        )
    )

    .withColumn(
        "source_file",
        input_file_name()
    )

    .withColumn(
        "ingestion_timestamp",
        current_timestamp()
    )

    .withColumn(
        "ano",
        year(col("purchase_date"))
    )

    .withColumn(
        "mes",
        month(col("purchase_date"))
    )

    .withColumn(
        "dia",
        dayofmonth(col("purchase_date"))
    )
)


bronze_count = df_bronze.count()


# ============================================================
# SILVER
#
# Curadoria:
# - padronizacao de strings
# - validacao de campos essenciais
# - validacao de dominios
# - deduplicacao por order_id
# ============================================================

df_silver = (
    df_bronze

    .withColumn(
        "customer_name",
        trim(col("customer_name"))
    )

    .withColumn(
        "customer_email",
        trim(col("customer_email"))
    )

    .withColumn(
        "cpf",
        trim(col("cpf"))
    )

    .withColumn(
        "product_name",
        trim(col("product_name"))
    )

    .withColumn(
        "category",
        trim(col("category"))
    )

    .withColumn(
        "city",
        trim(col("city"))
    )

    .withColumn(
        "state",
        upper(trim(col("state")))
    )

    .withColumn(
        "region",
        trim(col("region"))
    )

    .filter(
        col("order_id").isNotNull()
    )

    .filter(
        col("user_id").isNotNull()
    )

    .filter(
        col("product_id").isNotNull()
    )

    .filter(
        col("purchase_date").isNotNull()
    )

    .filter(
        col("quantity") > 0
    )

    .filter(
        col("order_status").isin(
            "Concluido",
            "Cancelado",
            "Devolvido"
        )
    )

    .filter(
        col("payment_method").isin(
            "Cartao",
            "Pix",
            "Boleto"
        )
    )

    .filter(
        col("sales_channel").isin(
            "Site",
            "App",
            "Marketplace"
        )
    )

    .dropDuplicates(
        ["order_id"]
    )
)


silver_count = df_silver.count()

removidos = bronze_count - silver_count


# ============================================================
# ESCRITA BRONZE
# ============================================================

(
    df_bronze.write
    .mode("overwrite")
    .option("compression", "snappy")
    .partitionBy(
        "ano",
        "mes"
    )
    .parquet(
        bronze_path
    )
)


# ============================================================
# ESCRITA SILVER
# ============================================================

(
    df_silver.write
    .mode("overwrite")
    .option("compression", "snappy")
    .partitionBy(
        "ano",
        "mes"
    )
    .parquet(
        silver_path
    )
)


# ============================================================
# RESULTADO
# ============================================================

print()
print("========================================")
print("CONTROLE DE REGISTROS")
print("========================================")

print(f"RAW: {raw_count}")
print(f"BRONZE: {bronze_count}")
print(f"SILVER: {silver_count}")
print(f"REMOVIDOS: {removidos}")

print()
print("Formato destino: Parquet")
print("Compressao: Snappy")
print("Particionamento: ano / mes")

job.commit()

print()
print("PROCESSAMENTO CONCLUIDO COM SUCESSO")
