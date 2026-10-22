{#
    Nom du dataset d'un modèle : <dataset de la cible>_<schéma du dossier>.
    Cible prod (dataset « ads ») : ads_staging, ads_marts, les datasets créés par Terraform.
    Cible dev (dataset « ads_dev ») : ads_dev_staging, ads_dev_marts, créés par dbt.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ target.schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
