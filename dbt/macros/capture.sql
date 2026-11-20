{% macro capture_id() -%}
  {% set value = env_var('WWI_DBT_CAPTURE_ID') %}
  {% if not modules.re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', value) %}
    {{ exceptions.raise_compiler_error('WWI_DBT_CAPTURE_ID must be an explicit canonical UUID') }}
  {% endif %}
  {{ return("'" ~ value ~ "'::uuid") }}
{%- endmacro %}

{% macro generate_schema_name(custom_schema_name, node) -%}
  {% set allowed = ['dw_staging','dw_intermediate','dw_core','sales_marts'] %}
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
    {% set result = run_query("select dw_staging.assert_capture(" ~ capture_id() ~ ")") %}
  {% endif %}
  {{ return('select 1') }}
{% endmacro %}

{% macro observed_key(kind, natural_key) -%}
  md5('{{ kind }}:OBSERVED_CAPTURE:' || {{ capture_id() }}::text || ':' || ({{ natural_key }})::text)
{%- endmacro %}
