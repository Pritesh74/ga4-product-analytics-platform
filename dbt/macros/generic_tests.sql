{% test not_negative(model, column_name) %}
-- Fails if any non-null value in column_name is less than zero.
select *
from {{ model }}
where {{ column_name }} is not null
  and {{ column_name }} < 0
{% endtest %}


{% test is_valid_date(model, column_name, min_date, max_date) %}
-- Fails if any date falls outside the expected dataset window.
select *
from {{ model }}
where {{ column_name }} is not null
  and (
      {{ column_name }} < date('{{ min_date }}')
      or {{ column_name }} > date('{{ max_date }}')
  )
{% endtest %}
