{{ config(pre_hook='{{ enforce_quality_gate() }}') }}
select invoice_id as source_invoice_id, order_id as source_order_id,invoice_date,
 to_char(invoice_date,'YYYYMMDD')::integer as invoice_date_key,
 customer_id as source_buyer_customer_id,bill_to_customer_id as source_bill_to_customer_id,
 {{ observed_key('CUSTOMER','customer_id') }} as buyer_observed_customer_key,
 {{ observed_key('CUSTOMER','bill_to_customer_id') }} as bill_to_observed_customer_key,
 null::text as buyer_customer_key,null::text as bill_to_customer_key,
 'U'::text as buyer_lookup_status,'U'::text as bill_to_lookup_status,
 'HISTORICAL_SCD2_DEFERRED'::text as historical_lookup_reason,
 is_credit_note,confirmed_delivery_time, _capture_id,record_identity,source_object,source_business_key,_raw_row_ordinal,
 ruleset_version,evaluation_id,{{ measure_version() }} as measure_version,
 q.dq_status,q.is_valid,q.has_warning,q.is_quarantined,q.is_valid as is_sales_eligible
from {{ ref('stg_sales_invoices') }}

join {{ ref('record_status') }} q using(record_identity,ruleset_version,evaluation_id,source_object,source_business_key,_raw_row_ordinal)
