{{ config(materialized='view') }}

select
    cast(order_id as varchar) as id_pedido,
    cast(user_id as varchar) as id_cliente,

    {{ limpar_string('customer_name') }} as nome_cliente,
    lower(trim(customer_email)) as email_cliente,
    trim(cpf) as cpf,

    cast(product_id as varchar) as id_produto,
    {{ limpar_string('product_name') }} as nome_produto,
    {{ limpar_string('category') }} as categoria_produto,

    cast(quantity as integer) as quantidade,
    cast(unit_price as decimal(12,2)) as preco_unitario,
    cast(price_rs as decimal(12,2)) as preco_original,
    cast(discount_pct as integer) as percentual_desconto,
    cast(final_price_rs as decimal(12,2)) as preco_final,

    {{ limpar_string('payment_method') }} as metodo_pagamento,
    {{ limpar_string('order_status') }} as status_pedido,
    {{ limpar_string('sales_channel') }} as canal_venda,

    cast(purchase_date as date) as data_compra,

    {{ limpar_string('city') }} as cidade,
    upper(trim(state)) as uf,
    {{ limpar_string('region') }} as regiao,

    cast(shipping_cost as decimal(12,2)) as valor_frete,
    cast(delivery_days as integer) as dias_entrega,

    source_file as arquivo_origem,
    ingestion_timestamp as data_hora_ingestao,
    cast(dia as integer) as dia

from {{ source('raw', 'vendas_silver_stage') }}
