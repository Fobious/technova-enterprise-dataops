{{ config(materialized='table') }}

select
    id_pedido,
    id_cliente,
    id_produto,
    metodo_pagamento as id_pagamento,
    cast(date_format(data_compra, '%Y%m%d') as integer) as id_tempo,

    data_compra,
    mes_referencia,
    regiao,

    preco_original,
    percentual_desconto,
    valor_desconto_real,
    preco_final,
    flag_teve_desconto

from {{ ref('ref_vendas_enriquecidas') }}