{#
    Premier jour retraité par un modèle incrémental : `reprocess_from` s'il est fourni,
    sinon les `lookback_days` derniers jours (les plateformes corrigent leurs chiffres après coup).
#}
{% macro incremental_start_date() -%}
    {%- set reprocess_from = var('reprocess_from') -%}
    {%- if reprocess_from -%}
        date '{{ reprocess_from }}'
    {%- else -%}
        date_sub(current_date(), interval {{ var('lookback_days') }} day)
    {%- endif -%}
{%- endmacro %}
