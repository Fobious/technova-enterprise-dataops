{{ config(materialized='view') }}

with vendas as (

    select *
    from {{ ref('stg_vendas') }}

),

regras_negocio as (

    select
        *,
        round(preco_original - preco_final, 2) as valor_desconto_real,

        case
            when percentual_desconto > 0 then true
            else false
        end as flag_teve_desconto,

        to_char(data_compra, 'YYYY-MM') as mes_referencia

    from vendas

)

select *
from regras_negocio