{% macro get_event_param(param_name, value_type='string_value') %}
    (
        select value.{{ value_type }}
        from unnest(event_params)
        where key = '{{ param_name }}'
    )
{% endmacro %}
