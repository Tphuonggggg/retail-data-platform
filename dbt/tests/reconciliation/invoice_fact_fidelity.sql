with expected as (
select l."InvoiceLineID" as id,l."InvoiceID" as invoice_id,l."StockItemID" as product_id,
 l."Quantity" as quantity,l."UnitPrice" as price,l."TaxAmount" as tax,
 l."ExtendedPrice"-l."TaxAmount" as amount,l."ExtendedPrice" as including_tax,
 i."InvoiceDate" as invoice_date,i."CustomerID" as buyer,i."BillToCustomerID" as bill_to
from {{ source('wwi_raw','sales_invoicelines') }} l left join {{ source('wwi_raw','sales_invoices') }} i
 on l."InvoiceID"=i."InvoiceID" and l._run_id=i._run_id where l._run_id={{ capture_id() }}
), actual as (
select source_invoice_line_id as id,source_invoice_id as invoice_id,source_stock_item_id as product_id,
 quantity,unit_price as price,tax_amount as tax,invoiced_sales_before_tax as amount,
 invoice_amount_including_tax as including_tax,invoice_date,
 source_buyer_customer_id as buyer,source_bill_to_customer_id as bill_to
from {{ ref('fact_invoice_line') }}
)
(select * from expected except all select * from actual)
union all (select * from actual except all select * from expected)
