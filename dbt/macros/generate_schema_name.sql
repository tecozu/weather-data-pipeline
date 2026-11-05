{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}

{% test expression_is_true(model, expression, column_name=none) %}
    select * from {{ model }} where not ({{ expression }})
{% endtest %}
