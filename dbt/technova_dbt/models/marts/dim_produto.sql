{{ config(materialized='table') }}

select distinct
    id_produto,
    nome_produto,
    categoria_produto as categoria
from {{ ref('ref_vendas_enriquecidas') }}
where id_produto is not null