-- PROPOSAL ONLY. Not an active dbt model. Do not execute without separate Owner approval.
-- Proposed new BI object: sales_marts.mart_order_invoice_reference (view).
-- Grain: one eligible source_order_id / _capture_id, OrderDate cohort.
-- Future owner/executor: retail_transform; SELECT for retail_bi_reader on this view only.
-- Requires a separate approved 13-object BI contract and regression/permissions update.
with invoiced_orders as (
    select distinct source_order_id, _capture_id
    from {{ ref('int_invoice_header') }}
    where is_sales_eligible and source_order_id is not null
)
select h.source_order_id, h.order_date, h.order_date_key,
       h.source_buyer_customer_id, h.buyer_observed_customer_key,
       s.backorder_order_id,
       (i.source_order_id is not null) as has_direct_invoice_reference,
       (child.source_order_id is not null) as linked_order_has_invoice_reference,
       case when i.source_order_id is not null then 'DIRECT_INVOICE_REFERENCE'
            when child.source_order_id is not null then 'LINKED_ORDER_HAS_INVOICE_REFERENCE'
            when s.backorder_order_id is not null then 'LINK_WITHOUT_CAPTURED_INVOICE_REFERENCE'
            else 'NO_DIRECT_OR_BACKORDER_REFERENCE' end as reference_class,
       h._capture_id, h.ruleset_version, h.measure_version
from {{ ref('int_order_header') }} h
join {{ ref('stg_sales_orders') }} s
  on s.order_id=h.source_order_id and s._capture_id=h._capture_id
left join invoiced_orders i
  on i.source_order_id=h.source_order_id and i._capture_id=h._capture_id
left join invoiced_orders child
  on child.source_order_id=s.backorder_order_id and child._capture_id=h._capture_id
where h.is_order_eligible
-- Reference classes do NOT assert fulfillment completion or a lost-sale status.
