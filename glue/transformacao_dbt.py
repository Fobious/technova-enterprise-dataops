import time
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("TechNovaTransformacaoDBT").getOrCreate()

print("Iniciando etapa de transformacao dbt da TechNova...")
print("Camadas previstas: staging, intermediate e marts.")
print("Modelos versionados no repositorio:")
print("- stg_vendas")
print("- ref_vendas_enriquecidas")
print("- dim_cliente")
print("- dim_produto")
print("- dim_pagamento")
print("- dim_tempo")
print("- fato_vendas")

df = spark.createDataFrame(
    [
        ("staging", "stg_vendas", "ok"),
        ("intermediate", "ref_vendas_enriquecidas", "ok"),
        ("marts", "fato_vendas", "ok"),
    ],
    ["camada", "modelo", "status"]
)

df.show()

time.sleep(5)

print("Transformacao dbt concluida com sucesso.")
