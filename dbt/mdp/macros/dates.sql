{#- Opérations sur des colonnes DATE, sans conversion implicite en DATETIME/TIMESTAMP : comparer une DATE à un
    DATETIME est une erreur BigQuery, et `dbt.dateadd` / `dbt.date_trunc` retournent justement ces types. -#}

{% macro date_offset(date_expr, days) -%}
    {{ return(adapter.dispatch('date_offset', 'mdp')(date_expr, days)) }}
{%- endmacro %}

{% macro default__date_offset(date_expr, days) -%}
    cast({{ date_expr }} + interval '{{ days }} day' as date)
{%- endmacro %}

{% macro bigquery__date_offset(date_expr, days) -%}
    date_add({{ date_expr }}, interval {{ days }} day)
{%- endmacro %}

{% macro month_start(date_expr) -%}
    {{ return(adapter.dispatch('month_start', 'mdp')(date_expr)) }}
{%- endmacro %}

{% macro default__month_start(date_expr) -%}
    cast(date_trunc('month', {{ date_expr }}) as date)
{%- endmacro %}

{% macro bigquery__month_start(date_expr) -%}
    date_trunc({{ date_expr }}, month)
{%- endmacro %}
