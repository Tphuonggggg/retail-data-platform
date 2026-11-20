"""Reviewable forward-only migration generator; never executes SQL."""
from ingestion.common.contracts import contract_hash, pg_quote
from ingestion.incremental import objects, ALGORITHM, MAX_DEPTH


def migration() -> str:
    scope=','.join("'"+o.name+"'" for o in objects())
    parts=[r'\set ON_ERROR_STOP on', 'BEGIN;', """
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
""",f"""
CREATE TABLE ingestion_meta.incremental_versions (
 version_id uuid PRIMARY KEY,
 parent_id uuid NOT NULL CHECK(parent_id<>version_id),
 base_run_id uuid NOT NULL REFERENCES ingestion_meta.runs(run_id),
 depth integer NOT NULL CHECK(depth BETWEEN 1 AND {MAX_DEPTH}),
 contract_hash text NOT NULL CHECK(contract_hash='{contract_hash()}'),
 algorithm text NOT NULL CHECK(algorithm='{ALGORITHM}'),
 status text NOT NULL DEFAULT 'RUNNING' CHECK(status IN ('RUNNING','VALIDATED','FAILED')),
 source_context jsonb NOT NULL,
 evidence jsonb NOT NULL DEFAULT '{{}}'::jsonb,
 error_code text,
 started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 finished_at timestamptz,
 -- No ACK mechanism is authorized by this candidate-only migration.
 acknowledged_publication_id uuid CHECK(acknowledged_publication_id IS NULL),
 CHECK((status='RUNNING' AND finished_at IS NULL) OR (status<>'RUNNING' AND finished_at IS NOT NULL))
);
CREATE TABLE ingestion_meta.incremental_events (
 version_id uuid NOT NULL REFERENCES ingestion_meta.incremental_versions(version_id),
 object_name text NOT NULL CHECK(object_name IN ({scope})),
 business_key integer NOT NULL,
 change_type text NOT NULL CHECK(change_type IN ('INSERT','UPDATE','DELETE')),
 before_version uuid NOT NULL,
 before_fingerprint text CHECK(before_fingerprint ~ '^[0-9a-f]{{64}}$'),
 after_fingerprint text CHECK(after_fingerprint ~ '^[0-9a-f]{{64}}$'),
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
"""]
    for obj in objects():
        delta='raw.'+pg_quote('delta_'+obj.target)
        key=pg_quote(obj.primary_key)
        fields=','.join('p.'+pg_quote(c.name) for c in obj.columns)
        changed_fields=','.join('d.'+pg_quote(c.name) for c in obj.columns)
        func='raw.'+pg_quote('sales_state_'+obj.target)
        parts.append(f"""
-- LIKE copies exact types/checks/indexes, but never existing rows or foreign keys.
CREATE TABLE {delta} (LIKE {obj.pg_table} INCLUDING ALL);
ALTER TABLE {delta} ADD FOREIGN KEY(_run_id) REFERENCES ingestion_meta.incremental_versions(version_id);
GRANT SELECT,INSERT ON {delta} TO retail_ingest;
GRANT SELECT ON {delta} TO retail_transform;
CREATE TRIGGER incremental_payload_guard BEFORE INSERT ON {delta}
 FOR EACH ROW EXECUTE FUNCTION ingestion_meta.guard_incremental_append('payload');
CREATE FUNCTION {func}(requested uuid) RETURNS SETOF {obj.pg_table}
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $state$
 WITH RECURSIVE chain AS (
   SELECT v.version_id,v.parent_id,v.base_run_id,0 AS distance
   FROM ingestion_meta.incremental_versions v WHERE v.version_id=requested AND v.status='VALIDATED'
   UNION ALL
   SELECT p.version_id,p.parent_id,p.base_run_id,c.distance+1
   FROM ingestion_meta.incremental_versions p JOIN chain c ON p.version_id=c.parent_id
   WHERE p.status='VALIDATED' AND c.distance<{MAX_DEPTH}
 ), latest AS (
   SELECT DISTINCT ON(e.business_key) e.business_key,e.version_id,e.change_type
   FROM ingestion_meta.incremental_events e JOIN chain c ON c.version_id=e.version_id
   WHERE e.object_name='{obj.name}' ORDER BY e.business_key,c.distance
 ), root AS (
   SELECT coalesce((SELECT base_run_id FROM chain WHERE distance=0),requested) AS run_id
 )
 SELECT requested,p.{key}::bigint+2147483649,{fields} FROM {obj.pg_table} p JOIN root r ON p._run_id=r.run_id
 WHERE NOT EXISTS(SELECT FROM latest e WHERE e.business_key=p.{key})
 UNION ALL
 SELECT requested,d.{key}::bigint+2147483649,{changed_fields} FROM latest e
 JOIN {delta} d ON d._run_id=e.version_id AND d.{key}=e.business_key
 WHERE e.change_type<>'DELETE'
$state$;
REVOKE ALL ON FUNCTION {func}(uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION {func}(uuid) TO retail_ingest,retail_transform;
""")
    parts.append(f"""
CREATE FUNCTION ingestion_meta.assert_sales_version(requested uuid) RETURNS void
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE v record; p record; root_id uuid; x record; actual bigint;
BEGIN
 SELECT * INTO v FROM ingestion_meta.incremental_versions WHERE version_id=requested;
 IF NOT FOUND THEN
   root_id := requested;
 ELSE
 root_id := v.base_run_id;
 IF v.status<>'VALIDATED' OR v.contract_hash<>'{contract_hash()}' OR v.algorithm<>'{ALGORITHM}'
 OR v.evidence->>'consistency' NOT IN ('UNVERIFIED','VERIFIED_FIXTURE')
 OR (SELECT count(*) FROM jsonb_object_keys(v.evidence->'objects'))<>6
 OR NOT (v.evidence->'objects' ?& ARRAY[{scope}])
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
   AND c.contract_hash='{contract_hash()}' AND c.source_context->>'database'='WideWorldImporters'
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
""")
    return '\n'.join(parts)


if __name__=='__main__':print(migration(),end='')
