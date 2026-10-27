{{ config(materialized='table') }}

select distinct
    cast(to_char(data_compra, 'YYYYMMDD') as integer) as id_tempo,
    data_compra as data_completa,
    extract(year from data_compra) as ano,
    extract(month from data_compra) as mes,
    extract(day from data_compra) as dia,
    mes_referencia
from {{ ref('ref_vendas_enriquecidas') }}
where data_compra is not null
