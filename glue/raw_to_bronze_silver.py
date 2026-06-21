import sys
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, year, month, dayofmonth, to_date


args = getResolvedOptions(
    sys.argv,
    [
        "RAW_BUCKET",
        "BRONZE_BUCKET",
        "SILVER_BUCKET"
    ]
)

RAW_BUCKET = args["RAW_BUCKET"]
BRONZE_BUCKET = args["BRONZE_BUCKET"]
SILVER_BUCKET = args["SILVER_BUCKET"]

spark = SparkSession.builder.appName("TechNovaRawToBronzeSilver").getOrCreate()

input_path = f"s3://{RAW_BUCKET}/ecommerce_dataset.csv"
bronze_path = f"s3://{BRONZE_BUCKET}/dados_vendas/"
silver_path = f"s3://{SILVER_BUCKET}/vendas_curadas/"

df_raw = (
    spark.read
    .option("header", "true")
    .option("inferSchema", "true")
    .csv(input_path)
)

df_tratado = (
    df_raw
    .withColumn("purchase_date", to_date(col("purchase_date"), "yyyy-MM-dd"))
    .withColumn("ano", year(col("purchase_date")))
    .withColumn("mes", month(col("purchase_date")))
    .withColumn("dia", dayofmonth(col("purchase_date")))
    .withColumn("price_rs", col("price_rs").cast("double"))
    .withColumn("discount_pct", col("discount_pct").cast("int"))
    .withColumn("final_price_rs", col("final_price_rs").cast("double"))
)

(
    df_tratado.write
    .mode("overwrite")
    .partitionBy("ano", "mes", "dia")
    .parquet(bronze_path)
)

df_silver = df_tratado.select(
    "order_id",
    "user_id",
    "customer_name",
    "customer_email",
    "cpf",
    "product_id",
    "product_name",
    "category",
    "price_rs",
    "discount_pct",
    "final_price_rs",
    "payment_method",
    "purchase_date",
    "region",
    "ano",
    "mes",
    "dia"
)

(
    df_silver.write
    .mode("overwrite")
    .partitionBy("ano", "mes", "dia")
    .parquet(silver_path)
)

print("Processamento TechNova concluído com sucesso.")
print(f"Arquivo origem: {input_path}")
print(f"Camada Bronze: {bronze_path}")
print(f"Camada Silver: {silver_path}")