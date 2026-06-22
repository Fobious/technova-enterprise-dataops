import sys
import time
import boto3
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ["DATABASE", "ATHENA_OUTPUT"])

DATABASE = args["DATABASE"]
ATHENA_OUTPUT = args["ATHENA_OUTPUT"]

athena = boto3.client("athena", region_name="us-east-1")

queries = [
    f"""
    CREATE OR REPLACE VIEW {DATABASE}.vw_faturamento_mensal AS
    SELECT
        date_format(CAST(purchase_date AS date), '%Y-%m') AS mes_referencia,
        COUNT(*) AS total_pedidos,
        ROUND(SUM(final_price_rs), 2) AS faturamento_total
    FROM {DATABASE}.vendas_curadas
    GROUP BY date_format(CAST(purchase_date AS date), '%Y-%m')
    """,

    f"""
    CREATE OR REPLACE VIEW {DATABASE}.vw_top_produtos AS
    SELECT
        product_name,
        category,
        COUNT(*) AS total_pedidos,
        ROUND(SUM(final_price_rs), 2) AS faturamento_total
    FROM {DATABASE}.vendas_curadas
    GROUP BY product_name, category
    """,

    f"""
    CREATE OR REPLACE VIEW {DATABASE}.vw_features_clientes_ml AS
    SELECT
        user_id,
        region,
        COUNT(order_id) AS qtd_pedidos,
        ROUND(SUM(final_price_rs), 2) AS valor_total_compras,
        ROUND(AVG(final_price_rs), 2) AS ticket_medio,
        MAX(CAST(purchase_date AS date)) AS ultima_compra
    FROM {DATABASE}.vendas_curadas
    GROUP BY user_id, region
    """
]

def wait_query(query_execution_id):
    while True:
        response = athena.get_query_execution(QueryExecutionId=query_execution_id)
        status = response["QueryExecution"]["Status"]["State"]

        if status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
            return status, response

        time.sleep(2)

for query in queries:
    print("Executando query Athena:")
    print(query)

    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": ATHENA_OUTPUT}
    )

    execution_id = response["QueryExecutionId"]
    status, final_response = wait_query(execution_id)

    print(f"Status da query: {status}")

    if status != "SUCCEEDED":
        raise Exception(f"Falha ao atualizar view Athena: {final_response}")

print("Views Athena atualizadas com sucesso.")
