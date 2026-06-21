{{ config(materialized='table') }}

select distinct
    metodo_pagamento as id_pagamento,
    metodo_pagamento as tipo_pagamento
from {{ ref('ref_vendas_enriquecidas') }}
where metodo_pagamento is not null