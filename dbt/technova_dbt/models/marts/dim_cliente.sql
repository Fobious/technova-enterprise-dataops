{{ config(materialized='table') }}

select distinct
    id_cliente,
    nome_cliente,
    email_cliente,
    cpf,
    cidade,
    uf,
    regiao
from {{ ref('ref_vendas_enriquecidas') }}
where id_cliente is not null
