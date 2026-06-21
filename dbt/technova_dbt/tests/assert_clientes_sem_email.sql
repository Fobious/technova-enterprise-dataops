select
    id_cliente,
    email_cliente
from {{ ref('dim_cliente') }}
where email_cliente is null
   or trim(email_cliente) = ''
   or email_cliente not like '%@%'
-- clientes sem email ou com email inválido, o que pode indicar dados incompletos ou incorretos.