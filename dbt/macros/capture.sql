{% macro capture_id() -%}
  {% set value = env_var('WWI_DBT_CAPTURE_ID') %}
  {% if not modules.re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', value) %}
    {{ exceptions.raise_compiler_error('WWI_DBT_CAPTURE_ID must be an explicit canonical UUID') }}
  {% endif %}
  {{ return("'" ~ value ~ "'::uuid") }}
{%- endmacro %}

{% macro generate_schema_name(custom_schema_name, node) -%}
  {% set allowed = ['dw_staging','dw_intermediate','dw_core','sales_marts','dq'] %}
  {% if node.resource_type == 'test' %}{{ return(target.schema) }}{% endif %}
  {% if custom_schema_name is none %}{% set custom_schema_name = target.schema %}{% endif %}
  {% if custom_schema_name not in allowed %}
    {{ exceptions.raise_compiler_error('Only dedicated warehouse schemas are allowed') }}
  {% endif %}
  {{ custom_schema_name }}
{%- endmacro %}

{% macro validate_capture() %}
  {% if execute %}
    {% set result = run_query("select current_database(),current_user") %}
    {% if result.rows[0][0] != 'retail_raw' or result.rows[0][1] != 'retail_transform' %}
      {{ exceptions.raise_compiler_error('Unexpected warehouse database or transformation identity') }}
    {% endif %}
    {% set settings = run_query("select current_setting('work_mem'),current_setting('max_parallel_workers_per_gather'),current_setting('jit')") %}
    {% if settings.rows[0][0] != (var('sales_work_mem_mb',4)|string ~ 'MB') or settings.rows[0][1] != '0' or settings.rows[0][2] != 'off' %}
      {{ exceptions.raise_compiler_error('Required session performance settings not active') }}
    {% endif %}
    {% set assertion = 'ingestion_meta.assert_sales_version' if var('sales_input_kind','FULL') == 'INCREMENTAL' else 'dw_staging.assert_capture' %}
    {% set result = run_query("select " ~ assertion ~ "(" ~ capture_id() ~ ")") %}
  {% endif %}
  {{ return('select 1') }}
{% endmacro %}

{% macro sales_raw_input(name) -%}
  {% set allowed = ['sales_customers','sales_orders','sales_orderlines','sales_invoices','sales_invoicelines','warehouse_stockitems'] %}
  {% if name not in allowed %}{{ exceptions.raise_compiler_error('Unregistered Sales source') }}{% endif %}
  {% set relation = source('wwi_raw',name) %}
  {% if var('sales_input_kind','FULL') == 'INCREMENTAL' %}
    {{ return('raw.sales_state_' ~ name ~ '(' ~ capture_id() ~ ')') }}
  {% elif var('sales_input_kind','FULL') == 'FULL' %}
    {{ return(relation) }}
  {% else %}{{ exceptions.raise_compiler_error('Unknown Sales input kind') }}{% endif %}
{%- endmacro %}

{% macro observed_key(kind, natural_key) -%}
  md5('{{ kind }}:OBSERVED_CAPTURE:' || {{ capture_id() }}::text || ':' || ({{ natural_key }})::text)
{%- endmacro %}

{% macro sql_literal(value) -%}
  {% if value is none %}NULL{% elif value is boolean %}{{ 'true' if value else 'false' }}
  {% elif value is number %}{{ value }}{% else %}'{{ value | replace("'", "''") }}'{% endif %}
{%- endmacro %}
{% macro ruleset() %}{{ return(sql_literal(var('sales_contract')['ruleset_version'])) }}{% endmacro %}
{% macro measure_version() %}{{ return(sql_literal(var('sales_contract')['measure_version'])) }}{% endmacro %}
{% macro evaluation_id() %}md5({{ capture_id() }}::text||':'||{{ ruleset() }}){% endmacro %}
{% macro ratio(numerator,denominator) %}(({{ numerator }})::numeric/nullif(({{ denominator }})::numeric,0)){% endmacro %}
{% macro metric(id) %}
 {% set registered={'S01':'count(*)','S02':'count(*)','S03':'sum(invoice_amount_including_tax)',
 'S04':'sum(tax_amount)','S05':'sum(invoiced_sales_before_tax)','UNITS':'sum(quantity)','C03':'sum(invoiced_sales_before_tax)'} %}
 {% if id not in registered %}{{ exceptions.raise_compiler_error('Unregistered aggregate measure') }}{% endif %}
 {{ return(registered[id]) }}
{% endmacro %}
{% macro customer_column() %}
 {{ return('source_buyer_customer_id' if var('sales_contract')['customer_role']=='BUYER' else 'source_bill_to_customer_id') }}
{% endmacro %}
{% macro build_metadata() %}
 {{ capture_id() }} as _capture_id,{{ ruleset() }} as ruleset_version,
 {{ evaluation_id() }} as evaluation_id,{{ measure_version() }} as measure_version,
 'DEVELOPMENT_UNCERTIFIED'::text as certification_status
{% endmacro %}
{% macro enforce_quality_gate() %}
 {% if execute %}
 {% set n=run_query("select count(*) from dq.validation_violations where action='fail_pipeline' and capture_id=" ~ capture_id() ~ " and ruleset_version=" ~ ruleset()) %}
 {% if n.rows[0][0]>0 %}{{ exceptions.raise_compiler_error('Fatal DQ violations persisted: downstream build blocked') }}{% endif %}
 {% endif %}
 {{ return('select 1') }}
{% endmacro %}
