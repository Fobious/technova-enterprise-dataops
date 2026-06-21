{% macro limpar_string(coluna) %}
    trim(regexp_replace({{ coluna }}, '\\s+', ' '))
{% endmacro %}