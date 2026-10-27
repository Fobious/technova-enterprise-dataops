-- TechNova Varejo
-- Tabela de origem utilizada pelo dbt no Amazon Redshift Serverless

CREATE TABLE IF NOT EXISTS technova_raw.vendas_curadas (
    order_id VARCHAR(20),
    user_id VARCHAR(20),
    customer_name VARCHAR(200),
    customer_email VARCHAR(200),
    cpf VARCHAR(20),
    product_id VARCHAR(20),
    product_name VARCHAR(200),
    category VARCHAR(100),
    price_rs DECIMAL(12,2),
    discount_pct INTEGER,
    final_price_rs DECIMAL(12,2),
    payment_method VARCHAR(50),
    purchase_date DATE,
    region VARCHAR(50)
);
