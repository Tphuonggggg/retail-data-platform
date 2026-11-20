select {{ observed_key('CUSTOMER','customer_id') }} as customer_key,
 customer_id as source_customer_id, customer_name, customer_category_id, buying_group_id,
 bill_to_customer_id as current_bill_to_customer_id,
 valid_from as source_valid_from, valid_to as source_valid_to,
 'OBSERVED_CURRENT_CAPTURE'::text as history_basis,
 true as is_observed_current, _capture_id
from {{ ref('stg_sales_customers') }}
