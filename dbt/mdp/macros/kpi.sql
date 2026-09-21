{#- Rapport protégé : NULL (et non une erreur ni 0) quand le dénominateur est nul ou absent.
    Calculé en flottant pour éviter toute division entière selon le moteur. -#}
{% macro safe_ratio(numerator, denominator, digits=4) -%}
    round(cast({{ numerator }} as {{ dbt.type_float() }}) / nullif({{ denominator }}, 0), {{ digits }})
{%- endmacro %}
