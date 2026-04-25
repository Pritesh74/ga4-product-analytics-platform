{% macro generate_date_spine(start_date, end_date) %}
    select date
    from unnest(
        generate_date_array(
            date('{{ start_date }}'),
            date('{{ end_date }}'),
            interval 1 day
        )
    ) as date
{% endmacro %}
