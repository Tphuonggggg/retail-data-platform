select l.invoice_line_id as source_invoice_line_id,l.invoice_id as source_invoice_id,
 h.source_order_id,h.invoice_date,h.invoice_date_key,
 h.source_buyer_customer_id,h.source_bill_to_customer_id,
 h.buyer_customer_key,h.bill_to_customer_key,
 h.buyer_observed_customer_key,h.bill_to_observed_customer_key,
 h.buyer_lookup_status,h.bill_to_lookup_status,h.historical_lookup_reason,
 l.stock_item_id as source_stock_item_id,
 {{ observed_key('PRODUCT','l.stock_item_id') }} as observed_product_key,
 null::text as product_key,'U'::text as product_lookup_status,
 'HISTORICAL_SCD2_DEFERRED'::text as product_lookup_reason,
 l.quantity,l.unit_price,
 (l.extended_price-l.tax_amount)::numeric as invoiced_sales_before_tax,
 l.tax_amount,l.extended_price as invoice_amount_including_tax,
 l.line_profit as source_reported_line_profit,h.is_credit_note,
 l.last_edited_when as source_last_edited_when,l._capture_id,l.record_identity,l.source_object,l.source_business_key,l._raw_row_ordinal,
 l.ruleset_version,l.evaluation_id,{{ measure_version() }} as measure_version,
 q.dq_status,q.is_valid,q.has_warning,q.is_quarantined,
 (q.is_valid and coalesce(h.is_sales_eligible,false)) as is_sales_eligible
from {{ ref('stg_sales_invoicelines') }} l
left join {{ ref('int_invoice_header') }} h
 on l.invoice_id=h.source_invoice_id and l._capture_id=h._capture_id

join {{ ref('record_status') }} q on q.record_identity=l.record_identity and q.ruleset_version=l.ruleset_version and q.evaluation_id=l.evaluation_id
