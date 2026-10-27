{{ config(materialized='table') }}

select
    id_pedido,
    id_cliente,
    id_produto,
    metodo_pagamento as id_pagamento,
    cast(to_char(data_compra, 'YYYYMMDD') as integer) as id_tempo,

    data_compra,
    mes_referencia,

    status_pedido,
    canal_venda,
    regiao,

    quantidade,
    preco_unitario,
    preco_original,
    percentual_desconto,
    valor_desconto_real,
    preco_final,
    valor_frete,
    dias_entrega,

    flag_teve_desconto

from {{ ref('ref_vendas_enriquecidas') }}
