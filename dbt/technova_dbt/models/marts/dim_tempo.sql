{{ config(materialized='table') }}

select distinct
    cast(date_format(data_compra, '%Y%m%d') as integer) as id_tempo,
    data_compra as data_completa,
    year(data_compra) as ano,
    month(data_compra) as mes,
    day(data_compra) as dia,
    mes_referencia
from {{ ref('ref_vendas_enriquecidas') }}
where data_compra is not null