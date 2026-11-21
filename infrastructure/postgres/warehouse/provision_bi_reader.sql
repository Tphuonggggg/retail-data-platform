BEGIN;

DO $guard$
BEGIN
    IF current_database() <> 'retail_raw'
       OR current_user <> 'postgres' THEN
        RAISE EXCEPTION 'Wrong database or operator';
    END IF;

    IF EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'retail_bi_reader'
    ) THEN
        RAISE EXCEPTION 'Role already exists; inspect before proceeding';
    END IF;
END
$guard$;

-- Chưa cho đăng nhập trước khi đặt mật khẩu riêng.
CREATE ROLE retail_bi_reader
    NOLOGIN NOINHERIT
    NOSUPERUSER NOCREATEDB NOCREATEROLE
    NOREPLICATION NOBYPASSRLS;

GRANT CONNECT ON DATABASE retail_raw
    TO retail_bi_reader;

GRANT USAGE ON SCHEMA
    dw_core, dw_intermediate, sales_marts
    TO retail_bi_reader;

GRANT SELECT ON TABLE
    dw_core.dim_date,
    dw_core.dim_customer,
    dw_core.dim_product,
    dw_core.fact_invoice_line,
    dw_core.fact_order_line,
    dw_intermediate.int_invoice_header,
    dw_intermediate.int_order_header,
    sales_marts.mart_sales_daily,
    sales_marts.mart_sales_monthly,
    sales_marts.mart_sales_product_daily,
    sales_marts.mart_customer_sales,
    sales_marts.mart_sales_customer_summary
    TO retail_bi_reader;

ALTER ROLE retail_bi_reader IN DATABASE retail_raw
    SET default_transaction_read_only = on;

ALTER ROLE retail_bi_reader IN DATABASE retail_raw
    SET search_path =
        pg_catalog, dw_core, sales_marts, dw_intermediate;

COMMIT;
