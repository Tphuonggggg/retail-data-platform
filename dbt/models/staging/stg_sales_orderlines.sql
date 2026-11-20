select _run_id as _capture_id, _row_ordinal as _raw_row_ordinal,
  cast("OrderLineID" as integer) as order_line_id,
  cast("OrderID" as integer) as order_id,
  cast("StockItemID" as integer) as stock_item_id,
  cast("Description" as text) as description,
  cast("PackageTypeID" as integer) as package_type_id,
  cast("Quantity" as integer) as quantity,
  cast("UnitPrice" as numeric(18,2)) as unit_price,
  cast("TaxRate" as numeric(18,3)) as tax_rate,
  cast("PickedQuantity" as integer) as picked_quantity,
  cast("PickingCompletedWhen" as text) collate "C" as picking_completed_when,
  cast("LastEditedBy" as integer) as last_edited_by,
  cast("LastEditedWhen" as text) collate "C" as last_edited_when
from {{ source('wwi_raw', 'sales_orderlines') }}
where _run_id = {{ capture_id() }}
