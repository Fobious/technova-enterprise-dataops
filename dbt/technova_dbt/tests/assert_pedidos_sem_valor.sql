select
    id_pedido,
    preco_final
from {{ ref('fato_vendas') }}
where preco_final is null
   or preco_final <= 0
-- pedidos sem valor ou com valor negativo, o que não faz sentido para uma venda válida.