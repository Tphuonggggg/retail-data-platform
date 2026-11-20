select _run_id as _capture_id, _row_ordinal as _raw_row_ordinal,
  cast("CustomerTransactionID" as integer) as customer_transaction_id,
  cast("CustomerID" as integer) as customer_id,
  cast("TransactionTypeID" as integer) as transaction_type_id,
  cast("InvoiceID" as integer) as invoice_id,
  cast("PaymentMethodID" as integer) as payment_method_id,
  cast("TransactionDate" as date) as transaction_date,
  cast("AmountExcludingTax" as numeric(18,2)) as amount_excluding_tax,
  cast("TaxAmount" as numeric(18,2)) as tax_amount,
  cast("TransactionAmount" as numeric(18,2)) as transaction_amount,
  cast("OutstandingBalance" as numeric(18,2)) as outstanding_balance,
  cast("FinalizationDate" as date) as finalization_date,
  cast("IsFinalized" as boolean) as is_finalized,
  cast("LastEditedBy" as integer) as last_edited_by,
  cast("LastEditedWhen" as text) collate "C" as last_edited_when
from {{ source('wwi_raw', 'sales_customertransactions') }}
where _run_id = {{ capture_id() }}
