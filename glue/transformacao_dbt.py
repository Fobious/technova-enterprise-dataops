import time

print("Iniciando etapa de transformação dbt da TechNova...")
print("Camadas previstas: staging, intermediate e marts.")
print("Modelos: stg_vendas, ref_vendas_enriquecidas, dim_cliente, dim_produto, dim_pagamento, dim_tempo e fato_vendas.")
print("Esta etapa representa a execução operacional da camada dbt dentro do workflow orquestrado.")
time.sleep(5)
print("Transformação dbt concluída com sucesso.")
