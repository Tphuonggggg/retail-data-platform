with expected as (
select l."OrderLineID" as id,l."OrderID" as order_id,l."StockItemID" as product_id,
 l."Quantity" as quantity,l."UnitPrice" as price,l."PickedQuantity" as picked,
 o."OrderDate" as order_date,o."CustomerID" as buyer
from {{ sales_raw_input('sales_orderlines') }} l left join {{ sales_raw_input('sales_orders') }} o
on o."OrderID"=l."OrderID" and o._run_id=l._run_id where l._run_id={{ capture_id() }}
), actual as (
select source_order_line_id as id,source_order_id as order_id,source_stock_item_id as product_id,
 ordered_quantity as quantity,source_unit_price as price,source_picked_quantity as picked,order_date,
 source_buyer_customer_id as buyer from {{ ref('fact_order_line') }}
)
(select * from expected except all select * from actual)
union all (select * from actual except all select * from expected)
