-- DW-IMPLEMENT-01: new-only, isolated warehouse schemas in the existing Raw DB.
-- Executed transactionally by provision.py, never by ordinary dbt commands.
DO $$ BEGIN
 IF current_database() <> 'retail_raw' OR current_user <> 'postgres'
 THEN RAISE EXCEPTION 'Wrong provisioning target'; END IF;
 IF EXISTS(SELECT FROM pg_roles WHERE rolname='retail_transform') OR
    EXISTS(SELECT FROM pg_namespace WHERE nspname IN
      ('dw_staging','dw_intermediate','dw_core','sales_marts'))
 THEN RAISE EXCEPTION 'Warehouse collision: inspect; do not rerun provisioning'; END IF;
END $$;
CREATE ROLE retail_transform NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
GRANT CONNECT ON DATABASE retail_raw TO retail_transform;
CREATE SCHEMA dw_staging AUTHORIZATION retail_transform;
CREATE SCHEMA dw_intermediate AUTHORIZATION retail_transform;
CREATE SCHEMA dw_core AUTHORIZATION retail_transform;
CREATE SCHEMA sales_marts AUTHORIZATION retail_transform;
GRANT USAGE ON SCHEMA raw,ingestion_meta TO retail_transform;
GRANT SELECT ON
 raw.sales_customers, raw.sales_customers_archive, raw.sales_orders,
 raw.sales_orderlines, raw.sales_invoices, raw.sales_invoicelines,
 raw.sales_customertransactions, raw.warehouse_stockitems,
 raw.warehouse_stockitems_archive, raw.warehouse_stockitemholdings,
 raw.warehouse_stockitemtransactions,
 ingestion_meta.runs, ingestion_meta.object_runs, ingestion_meta.load_contracts,
 ingestion_meta.load_audits, ingestion_meta.raw_publications, ingestion_meta.raw_current
 TO retail_transform;

-- Invoker-only read check: no authority to modify Raw or certify/publish a run.
CREATE FUNCTION dw_staging.assert_capture(requested uuid) RETURNS void
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE x record; actual bigint; expected_scope text[];
BEGIN
 expected_scope := ARRAY['Sales.CustomerTransactions','Sales.Customers',
  'Sales.Customers_Archive','Sales.InvoiceLines','Sales.Invoices','Sales.OrderLines',
  'Sales.Orders','Warehouse.StockItemHoldings','Warehouse.StockItemTransactions',
  'Warehouse.StockItems','Warehouse.StockItems_Archive'];
 IF NOT EXISTS(SELECT FROM ingestion_meta.runs r
    JOIN ingestion_meta.load_contracts c USING(run_id)
    WHERE r.run_id=requested AND r.status='SUCCEEDED' AND r.extraction_mode='FULL'
      AND c.scope=expected_scope
      AND c.contract_hash='73a9a8dfe786ff6fcec84a176cda0d9398184c85486369671c97d407eeb9e3c7'
      AND c.source_context->>'database'='WideWorldImporters')
 THEN RAISE EXCEPTION 'Missing, incomplete or incompatible capture'; END IF;
 IF (SELECT count(*) FROM ingestion_meta.object_runs WHERE run_id=requested)<>11
 OR (SELECT count(*) FROM ingestion_meta.load_audits WHERE run_id=requested)<>11
 THEN RAISE EXCEPTION 'Capture must contain all eleven reconciled objects'; END IF;
 FOR x IN SELECT * FROM (VALUES
   ('Sales','Customers','sales_customers'),('Sales','Customers_Archive','sales_customers_archive'),
   ('Sales','Orders','sales_orders'),('Sales','OrderLines','sales_orderlines'),
   ('Sales','Invoices','sales_invoices'),('Sales','InvoiceLines','sales_invoicelines'),
   ('Sales','CustomerTransactions','sales_customertransactions'),
   ('Warehouse','StockItems','warehouse_stockitems'),
   ('Warehouse','StockItems_Archive','warehouse_stockitems_archive'),
   ('Warehouse','StockItemHoldings','warehouse_stockitemholdings'),
   ('Warehouse','StockItemTransactions','warehouse_stockitemtransactions')
 ) AS objects(source_schema,source_table,target_table) LOOP
   EXECUTE format('SELECT count(*) FROM raw.%I WHERE _run_id=$1',x.target_table)
     INTO actual USING requested;
   IF NOT EXISTS(SELECT FROM ingestion_meta.object_runs o
      JOIN ingestion_meta.load_audits a ON a.run_id=o.run_id
       AND a.object_name=o.source_schema||'.'||o.source_table
      WHERE o.run_id=requested AND o.source_schema=x.source_schema
        AND o.source_table=x.source_table AND o.status='SUCCEEDED'
        AND o.reconciliation_state='PASS' AND o.source_row_count=actual
        AND o.extracted_row_count=actual AND o.loaded_row_count=actual AND a.row_count=actual)
   THEN RAISE EXCEPTION 'Capture population mismatch: %.%',x.source_schema,x.source_table; END IF;
 END LOOP;
END $$;
ALTER FUNCTION dw_staging.assert_capture(uuid) OWNER TO retail_transform;
REVOKE ALL ON FUNCTION dw_staging.assert_capture(uuid) FROM PUBLIC;
