\set ON_ERROR_STOP on
BEGIN;

DO $$ BEGIN
 IF current_database()<>'retail_raw' OR current_user<>'postgres'
 THEN RAISE EXCEPTION 'Wrong incremental provisioning identity/target'; END IF;
 IF EXISTS(SELECT FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
   WHERE (n.nspname='ingestion_meta' AND c.relname IN ('incremental_versions','incremental_events'))
      OR (n.nspname='raw' AND c.relname LIKE 'delta_%'))
 OR EXISTS(SELECT FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE (n.nspname='raw' AND p.proname LIKE 'sales_state_%')
      OR (n.nspname='ingestion_meta' AND p.proname='assert_sales_version'))
 THEN RAISE EXCEPTION 'Incremental object collision; inspect, never rerun blindly'; END IF;
 IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='retail_ingest' AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb)
 OR NOT EXISTS(SELECT FROM pg_roles WHERE rolname='retail_transform' AND NOT rolsuper AND NOT rolcreaterole AND NOT rolcreatedb)
 THEN RAISE EXCEPTION 'Expected existing non-admin roles'; END IF;
END $$;


CREATE TABLE ingestion_meta.incremental_versions (
 version_id uuid PRIMARY KEY,
 parent_id uuid NOT NULL CHECK(parent_id<>version_id),
 base_run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
 depth integer NOT NULL CHECK(depth BETWEEN 1 AND 32),
 contract_hash text NOT NULL CHECK(contract_hash='73a9a8dfe786ff6fcec84a176cda0d9398184c85486369671c97d407eeb9e3c7'),
 algorithm text NOT NULL CHECK(algorithm='sales-snapshot-diff-v1'),
 status text NOT NULL DEFAULT 'RUNNING' CHECK(status IN ('RUNNING','VALIDATED','FAILED')),
 source_context jsonb NOT NULL,
 evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
 error_code text,
 started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 finished_at timestamptz,
 -- No ACK mechanism is authorized by this candidate-only migration.
 acknowledged_publication_id uuid CHECK(acknowledged_publication_id IS NULL),
 CHECK((status='RUNNING' AND finished_at IS NULL) OR (status<>'RUNNING' AND finished_at IS NOT NULL))
);
CREATE TABLE ingestion_meta.incremental_events (
 version_id uuid NOT NULL REFERENCES ingestion_meta.incremental_versions(version_id),
 object_name text NOT NULL CHECK(object_name IN ('Sales.Customers','Sales.InvoiceLines','Sales.Invoices','Sales.OrderLines','Sales.Orders','Warehouse.StockItems')),
 business_key integer NOT NULL,
 change_type text NOT NULL CHECK(change_type IN ('INSERT','UPDATE','DELETE')),
 before_version uuid NOT NULL,
 before_fingerprint text CHECK(before_fingerprint ~ '^[0-9a-f]{64}$'),
 after_fingerprint text CHECK(after_fingerprint ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY(version_id,object_name,business_key),
 CHECK((change_type='INSERT' AND before_fingerprint IS NULL AND after_fingerprint IS NOT NULL)
    OR (change_type='UPDATE' AND before_fingerprint IS NOT NULL AND after_fingerprint IS NOT NULL)
    OR (change_type='DELETE' AND before_fingerprint IS NOT NULL AND after_fingerprint IS NULL))
);
GRANT SELECT,INSERT,UPDATE ON ingestion_meta.incremental_versions TO retail_ingest;
GRANT SELECT,INSERT ON ingestion_meta.incremental_events TO retail_ingest;
GRANT SELECT ON ingestion_meta.incremental_versions,ingestion_meta.incremental_events TO retail_transform;
CREATE FUNCTION ingestion_meta.guard_incremental_ledger() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='INSERT' THEN
   IF NEW.status<>'RUNNING' THEN RAISE EXCEPTION 'A new candidate must start RUNNING'; END IF;
 ELSE
   IF OLD.status<>'RUNNING' OR
     (to_jsonb(NEW)-ARRAY['status','evidence','error_code','finished_at']) IS DISTINCT FROM
     (to_jsonb(OLD)-ARRAY['status','evidence','error_code','finished_at'])
   THEN RAISE EXCEPTION 'Immutable candidate identity or terminal outcome'; END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER incremental_ledger_guard BEFORE INSERT OR UPDATE ON ingestion_meta.incremental_versions
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_ledger();
REVOKE ALL ON FUNCTION ingestion_meta.guard_incremental_ledger() FROM PUBLIC;
CREATE FUNCTION ingestion_meta.guard_incremental_append() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE requested uuid; candidate_status text;
BEGIN
 requested := (CASE WHEN TG_ARGV[0]='event' THEN to_jsonb(NEW)->>'version_id' ELSE to_jsonb(NEW)->>'_run_id' END)::uuid;
 SELECT status INTO candidate_status FROM ingestion_meta.incremental_versions WHERE version_id=requested FOR SHARE;
 IF candidate_status IS DISTINCT FROM 'RUNNING'
 THEN RAISE EXCEPTION 'Append requires an active candidate'; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER incremental_event_guard BEFORE INSERT ON ingestion_meta.incremental_events
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('event');
REVOKE ALL ON FUNCTION ingestion_meta.guard_incremental_append() FROM PUBLIC;


-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE raw."delta_sales_customers" (LIKE raw."sales_customers" INCLUDING ALL);
ALTER TABLE raw."delta_sales_customers" ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON raw."delta_sales_customers" TO retail_ingest;
GRANT SELECT ON raw."delta_sales_customers" TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON raw."delta_sales_customers"
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION raw."sales_state_sales_customers"(requested uuid) RETURNS SETOF raw."sales_customers"
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<32
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='Sales.Customers' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p."CustomerID"::bigint+2147483649,p."CustomerID",p."CustomerName",p."BillToCustomerID",p."CustomerCategoryID",p."BuyingGroupID",p."PrimaryContactPersonID",p."AlternateContactPersonID",p."DeliveryMethodID",p."DeliveryCityID",p."PostalCityID",p."CreditLimit",p."AccountOpenedDate",p."StandardDiscountPercentage",p."IsStatementSent",p."IsOnCreditHold",p."PaymentDays",p."PhoneNumber",p."FaxNumber",p."DeliveryRun",p."RunPosition",p."WebsiteURL",p."DeliveryAddressLine1",p."DeliveryAddressLine2",p."DeliveryPostalCode",p."DeliveryLocation",p."PostalAddressLine1",p."PostalAddressLine2",p."PostalPostalCode",p."LastEditedBy",p."ValidFrom",p."ValidTo" FROM raw."sales_customers" p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p."CustomerID")
 UNION ALL
 SELECT requested,d."CustomerID"::bigint+2147483649,d."CustomerID",d."CustomerName",d."BillToCustomerID",d."CustomerCategoryID",d."BuyingGroupID",d."PrimaryContactPersonID",d."AlternateContactPersonID",d."DeliveryMethodID",d."DeliveryCityID",d."PostalCityID",d."CreditLimit",d."AccountOpenedDate",d."StandardDiscountPercentage",d."IsStatementSent",d."IsOnCreditHold",d."PaymentDays",d."PhoneNumber",d."FaxNumber",d."DeliveryRun",d."RunPosition",d."WebsiteURL",d."DeliveryAddressLine1",d."DeliveryAddressLine2",d."DeliveryPostalCode",d."DeliveryLocation",d."PostalAddressLine1",d."PostalAddressLine2",d."PostalPostalCode",d."LastEditedBy",d."ValidFrom",d."ValidTo" FROM latest e
 JOIN raw."delta_sales_customers" d ON d._run_id=e.version_id AND d."CustomerID"=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION raw."sales_state_sales_customers"(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION raw."sales_state_sales_customers"(uuid) TO retail_ingest,retail_transform;


-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE raw."delta_sales_invoicelines" (LIKE raw."sales_invoicelines" INCLUDING ALL);
ALTER TABLE raw."delta_sales_invoicelines" ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON raw."delta_sales_invoicelines" TO retail_ingest;
GRANT SELECT ON raw."delta_sales_invoicelines" TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON raw."delta_sales_invoicelines"
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION raw."sales_state_sales_invoicelines"(requested uuid) RETURNS SETOF raw."sales_invoicelines"
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<32
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='Sales.InvoiceLines' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p."InvoiceLineID"::bigint+2147483649,p."InvoiceLineID",p."InvoiceID",p."StockItemID",p."Description",p."PackageTypeID",p."Quantity",p."UnitPrice",p."TaxRate",p."TaxAmount",p."LineProfit",p."ExtendedPrice",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_invoicelines" p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p."InvoiceLineID")
 UNION ALL
 SELECT requested,d."InvoiceLineID"::bigint+2147483649,d."InvoiceLineID",d."InvoiceID",d."StockItemID",d."Description",d."PackageTypeID",d."Quantity",d."UnitPrice",d."TaxRate",d."TaxAmount",d."LineProfit",d."ExtendedPrice",d."LastEditedBy",d."LastEditedWhen" FROM latest e
 JOIN raw."delta_sales_invoicelines" d ON d._run_id=e.version_id AND d."InvoiceLineID"=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION raw."sales_state_sales_invoicelines"(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION raw."sales_state_sales_invoicelines"(uuid) TO retail_ingest,retail_transform;


-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE raw."delta_sales_invoices" (LIKE raw."sales_invoices" INCLUDING ALL);
ALTER TABLE raw."delta_sales_invoices" ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON raw."delta_sales_invoices" TO retail_ingest;
GRANT SELECT ON raw."delta_sales_invoices" TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON raw."delta_sales_invoices"
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION raw."sales_state_sales_invoices"(requested uuid) RETURNS SETOF raw."sales_invoices"
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<32
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='Sales.Invoices' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p."InvoiceID"::bigint+2147483649,p."InvoiceID",p."CustomerID",p."BillToCustomerID",p."OrderID",p."DeliveryMethodID",p."ContactPersonID",p."AccountsPersonID",p."SalespersonPersonID",p."PackedByPersonID",p."InvoiceDate",p."CustomerPurchaseOrderNumber",p."IsCreditNote",p."CreditNoteReason",p."Comments",p."DeliveryInstructions",p."InternalComments",p."TotalDryItems",p."TotalChillerItems",p."DeliveryRun",p."RunPosition",p."ReturnedDeliveryData",p."ConfirmedDeliveryTime",p."ConfirmedReceivedBy",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_invoices" p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p."InvoiceID")
 UNION ALL
 SELECT requested,d."InvoiceID"::bigint+2147483649,d."InvoiceID",d."CustomerID",d."BillToCustomerID",d."OrderID",d."DeliveryMethodID",d."ContactPersonID",d."AccountsPersonID",d."SalespersonPersonID",d."PackedByPersonID",d."InvoiceDate",d."CustomerPurchaseOrderNumber",d."IsCreditNote",d."CreditNoteReason",d."Comments",d."DeliveryInstructions",d."InternalComments",d."TotalDryItems",d."TotalChillerItems",d."DeliveryRun",d."RunPosition",d."ReturnedDeliveryData",d."ConfirmedDeliveryTime",d."ConfirmedReceivedBy",d."LastEditedBy",d."LastEditedWhen" FROM latest e
 JOIN raw."delta_sales_invoices" d ON d._run_id=e.version_id AND d."InvoiceID"=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION raw."sales_state_sales_invoices"(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION raw."sales_state_sales_invoices"(uuid) TO retail_ingest,retail_transform;


-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE raw."delta_sales_orderlines" (LIKE raw."sales_orderlines" INCLUDING ALL);
ALTER TABLE raw."delta_sales_orderlines" ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON raw."delta_sales_orderlines" TO retail_ingest;
GRANT SELECT ON raw."delta_sales_orderlines" TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON raw."delta_sales_orderlines"
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION raw."sales_state_sales_orderlines"(requested uuid) RETURNS SETOF raw."sales_orderlines"
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<32
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='Sales.OrderLines' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p."OrderLineID"::bigint+2147483649,p."OrderLineID",p."OrderID",p."StockItemID",p."Description",p."PackageTypeID",p."Quantity",p."UnitPrice",p."TaxRate",p."PickedQuantity",p."PickingCompletedWhen",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_orderlines" p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p."OrderLineID")
 UNION ALL
 SELECT requested,d."OrderLineID"::bigint+2147483649,d."OrderLineID",d."OrderID",d."StockItemID",d."Description",d."PackageTypeID",d."Quantity",d."UnitPrice",d."TaxRate",d."PickedQuantity",d."PickingCompletedWhen",d."LastEditedBy",d."LastEditedWhen" FROM latest e
 JOIN raw."delta_sales_orderlines" d ON d._run_id=e.version_id AND d."OrderLineID"=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION raw."sales_state_sales_orderlines"(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION raw."sales_state_sales_orderlines"(uuid) TO retail_ingest,retail_transform;


-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE raw."delta_sales_orders" (LIKE raw."sales_orders" INCLUDING ALL);
ALTER TABLE raw."delta_sales_orders" ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON raw."delta_sales_orders" TO retail_ingest;
GRANT SELECT ON raw."delta_sales_orders" TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON raw."delta_sales_orders"
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION raw."sales_state_sales_orders"(requested uuid) RETURNS SETOF raw."sales_orders"
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<32
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='Sales.Orders' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p."OrderID"::bigint+2147483649,p."OrderID",p."CustomerID",p."SalespersonPersonID",p."PickedByPersonID",p."ContactPersonID",p."BackorderOrderID",p."OrderDate",p."ExpectedDeliveryDate",p."CustomerPurchaseOrderNumber",p."IsUndersupplyBackordered",p."Comments",p."DeliveryInstructions",p."InternalComments",p."PickingCompletedWhen",p."LastEditedBy",p."LastEditedWhen" FROM raw."sales_orders" p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p."OrderID")
 UNION ALL
 SELECT requested,d."OrderID"::bigint+2147483649,d."OrderID",d."CustomerID",d."SalespersonPersonID",d."PickedByPersonID",d."ContactPersonID",d."BackorderOrderID",d."OrderDate",d."ExpectedDeliveryDate",d."CustomerPurchaseOrderNumber",d."IsUndersupplyBackordered",d."Comments",d."DeliveryInstructions",d."InternalComments",d."PickingCompletedWhen",d."LastEditedBy",d."LastEditedWhen" FROM latest e
 JOIN raw."delta_sales_orders" d ON d._run_id=e.version_id AND d."OrderID"=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION raw."sales_state_sales_orders"(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION raw."sales_state_sales_orders"(uuid) TO retail_ingest,retail_transform;


-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE raw."delta_warehouse_stockitems" (LIKE raw."warehouse_stockitems" INCLUDING ALL);
ALTER TABLE raw."delta_warehouse_stockitems" ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON raw."delta_warehouse_stockitems" TO retail_ingest;
GRANT SELECT ON raw."delta_warehouse_stockitems" TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON raw."delta_warehouse_stockitems"
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION raw."sales_state_warehouse_stockitems"(requested uuid) RETURNS SETOF raw."warehouse_stockitems"
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<32
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='Warehouse.StockItems' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p."StockItemID"::bigint+2147483649,p."StockItemID",p."StockItemName",p."SupplierID",p."ColorID",p."UnitPackageID",p."OuterPackageID",p."Brand",p."Size",p."LeadTimeDays",p."QuantityPerOuter",p."IsChillerStock",p."Barcode",p."TaxRate",p."UnitPrice",p."RecommendedRetailPrice",p."TypicalWeightPerUnit",p."MarketingComments",p."InternalComments",p."Photo",p."CustomFields",p."Tags",p."SearchDetails",p."LastEditedBy",p."ValidFrom",p."ValidTo" FROM raw."warehouse_stockitems" p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p."StockItemID")
 UNION ALL
 SELECT requested,d."StockItemID"::bigint+2147483649,d."StockItemID",d."StockItemName",d."SupplierID",d."ColorID",d."UnitPackageID",d."OuterPackageID",d."Brand",d."Size",d."LeadTimeDays",d."QuantityPerOuter",d."IsChillerStock",d."Barcode",d."TaxRate",d."UnitPrice",d."RecommendedRetailPrice",d."TypicalWeightPerUnit",d."MarketingComments",d."InternalComments",d."Photo",d."CustomFields",d."Tags",d."SearchDetails",d."LastEditedBy",d."ValidFrom",d."ValidTo" FROM latest e
 JOIN raw."delta_warehouse_stockitems" d ON d._run_id=e.version_id AND d."StockItemID"=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION raw."sales_state_warehouse_stockitems"(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION raw."sales_state_warehouse_stockitems"(uuid) TO retail_ingest,retail_transform;


CREATE FUNCTION ingestion_meta.assert_sales_version(requested uuid) RETURNS void
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE v record; p record; root_id uuid; x record; actual bigint;
BEGIN
 SELECT * INTO v FROM ingestion_meta.incremental_versions WHERE version_id=requested;
 IF NOT FOUND THEN
   root_id := requested;
 ELSE
 root_id := v.base_run_id;
 IF v.status<>'VALIDATED' OR v.contract_hash<>'73a9a8dfe786ff6fcec84a176cda0d9398184c85486369671c97d407eeb9e3c7' OR v.algorithm<>'sales-snapshot-diff-v1'
 OR v.evidence->>'consistency' NOT IN ('UNVERIFIED','VERIFIED_FIXTURE')
 OR (SELECT count(*) FROM jsonb_object_keys(v.evidence->'objects'))<>6
 OR NOT (v.evidence->'objects' ?& ARRAY['Sales.Customers','Sales.InvoiceLines','Sales.Invoices','Sales.OrderLines','Sales.Orders','Warehouse.StockItems'])
 THEN RAISE EXCEPTION 'Missing/incomplete/incompatible incremental candidate'; END IF;
 -- A pinned candidate does not certify a source-consistent publication.
 IF v.parent_id=v.base_run_id THEN
   IF v.depth<>1 THEN RAISE EXCEPTION 'Invalid root depth'; END IF;
 ELSE
   SELECT * INTO p FROM ingestion_meta.incremental_versions WHERE version_id=v.parent_id;
   IF NOT FOUND OR p.status<>'VALIDATED' OR p.base_run_id<>v.base_run_id OR p.depth+1<>v.depth
   THEN RAISE EXCEPTION 'Invalid parent version'; END IF;
 END IF;
 END IF;
 IF NOT EXISTS(SELECT FROM ingestion_meta.runs r JOIN ingestion_meta.load_contracts c USING(run_id)
   WHERE r.run_id=root_id AND r.status='SUCCEEDED' AND r.extraction_mode='FULL'
   AND c.contract_hash='73a9a8dfe786ff6fcec84a176cda0d9398184c85486369671c97d407eeb9e3c7' AND c.source_context->>'database'='WideWorldImporters'
   AND c.scope=ARRAY['Sales.CustomerTransactions','Sales.Customers','Sales.Customers_Archive',
    'Sales.InvoiceLines','Sales.Invoices','Sales.OrderLines','Sales.Orders','Warehouse.StockItemHoldings',
    'Warehouse.StockItemTransactions','Warehouse.StockItems','Warehouse.StockItems_Archive'])
 OR (SELECT count(*) FROM ingestion_meta.object_runs WHERE run_id=root_id)<>11
 OR (SELECT count(*) FROM ingestion_meta.load_audits WHERE run_id=root_id)<>11
 THEN RAISE EXCEPTION 'Missing/incompatible Full Load base'; END IF;
 FOR x IN SELECT * FROM (VALUES
   ('Sales.Customers','sales_customers'),('Sales.InvoiceLines','sales_invoicelines'),
   ('Sales.Invoices','sales_invoices'),('Sales.OrderLines','sales_orderlines'),
   ('Sales.Orders','sales_orders'),('Warehouse.StockItems','warehouse_stockitems')
 ) AS objects(object_name,target_table) LOOP
   EXECUTE format('SELECT count(*) FROM raw.%I WHERE _run_id=$1',x.target_table) INTO actual USING root_id;
   IF NOT EXISTS(SELECT FROM ingestion_meta.object_runs o JOIN ingestion_meta.load_audits a
     ON a.run_id=o.run_id AND a.object_name=o.source_schema||'.'||o.source_table
     WHERE o.run_id=root_id AND a.object_name=x.object_name AND o.status='SUCCEEDED'
     AND o.reconciliation_state='PASS' AND o.source_row_count=actual AND o.extracted_row_count=actual
     AND o.loaded_row_count=actual AND a.row_count=actual)
   THEN RAISE EXCEPTION 'Base population mismatch'; END IF;
 END LOOP;
END $$;
REVOKE ALL ON FUNCTION ingestion_meta.assert_sales_version(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION ingestion_meta.assert_sales_version(uuid) TO retail_ingest,retail_transform;
COMMIT;
