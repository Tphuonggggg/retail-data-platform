select l.order_line_id as source_order_line_id,l.order_id as source_order_id,
 h.order_date,h.order_date_key,h.source_buyer_customer_id,
 h.buyer_customer_key,h.buyer_observed_customer_key,h.buyer_lookup_status,h.buyer_lookup_reason,
 l.stock_item_id as source_stock_item_id,
 {{ observed_key('PRODUCT','l.stock_item_id') }} as observed_product_key,
 null::text as product_key,'U'::text as product_lookup_status,
 'HISTORICAL_SCD2_DEFERRED'::text as product_lookup_reason,
 l.quantity as ordered_quantity,l.picked_quantity as source_picked_quantity,
 l.unit_price as source_unit_price,l.last_edited_when as source_last_edited_when,
 l._capture_id
from {{ ref('stg_sales_orderlines') }} l
left join {{ ref('int_order_header') }} h
 on l.order_id=h.source_order_id and l._capture_id=h._capture_id
