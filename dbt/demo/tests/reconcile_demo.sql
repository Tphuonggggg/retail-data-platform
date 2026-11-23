with expected(sales_date,sales_amount,units_sold) as (
 values (date '2024-01-01',45.00::numeric,6::bigint),(date '2024-01-02',10.00::numeric,1::bigint)
), actual as (select * from {{ ref('mart_demo_daily') }})
(select * from expected except select * from actual)
union all
(select * from actual except select * from expected)
