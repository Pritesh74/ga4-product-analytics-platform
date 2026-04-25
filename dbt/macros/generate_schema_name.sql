{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}

{#
  Override of dbt's default generate_schema_name.

  Default dbt behaviour:  target_dataset + '_' + custom_schema
    e.g. product_analytics_dev_ga4_staging

  This override:  use custom_schema as-is
    e.g. ga4_staging

  Result — dbt creates these datasets in your GCP project:
    ga4_staging        (staging views)
    ga4_intermediate   (intermediate views)
    ga4_marts          (mart tables)
    ga4_experiments    (experiment tables)
    product_analytics_dev  (default, used if no +schema is set)
#}
