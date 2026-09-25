{#- Séparation des environnements : en prod, mdp_<couche> (mdp_staging, mdp_marts…) ;
    ailleurs, <schéma de la cible>_<couche> (ex. mdp_dev_marts) pour ne jamais écrire dans la prod. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- elif target.name == 'prod' -%}
        mdp_{{ custom_schema_name | trim }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
