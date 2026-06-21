{{ config(materialized='view') }}

select
    cast(order_id as varchar) as id_pedido,
    cast(user_id as varchar) as id_cliente,
    {{ limpar_string('customer_name') }} as nome_cliente,
    lower(trim(customer_email)) as email_cliente,
    cpf,
    cast(product_id as varchar) as id_produto,
    {{ limpar_string('product_name') }} as nome_produto,
    {{ limpar_string('category') }} as categoria_produto,
    cast(price_rs as double) as preco_original,
    cast(discount_pct as integer) as percentual_desconto,
    cast(final_price_rs as double) as preco_final,
    {{ limpar_string('payment_method') }} as metodo_pagamento,
    cast(purchase_date as date) as data_compra,
    {{ limpar_string('region') }} as regiao
from {{ source('raw', 'vendas_curadas') }}