# Modèle de données

## Grain

**Une ligne = une campagne × un jour × une plateforme.** Clé : `(report_date, campaign_id, platform)`. Unicité testée dans staging, intermediate et marts.

## Zone raw

Colonnes communes : `date` (DATE, obligatoire), `campaign_id` (STRING, obligatoire), `campaign_name`, `impressions`, `clicks` (INT64, obligatoires), `conversions` (INT64), `conversion_value` (FLOAT64), puis les métadonnées `ingested_at`, `extract_run_id`, `source`, `data_mode`.

| Table | Colonnes propres |
|---|---|
| `google_ads_campaign_daily` | `cost_usd` |
| `meta_ads_campaign_daily` | `spend_usd`, `likes`, `comments`, `shares`, `video_views`, `page_engagement` |

Définition faisant foi : [`src/mdp/ingestion/schemas.py`](../src/mdp/ingestion/schemas.py).

**`conversions` et `conversion_value` sont nullables** : NULL signifie « la source ne suit pas cette métrique », 0 signifie « suivie, et il n'y en a pas eu ». Confondre les deux fausserait CPA et ROAS.

**`data_mode`** : `real` (API de la plateforme) ou `simulated` (données générées de façon déterministe).

## Marts

`mart_campaign_daily` (faits) : dimensions `report_date`, `campaign_id`, `campaign_name`, `platform`, `data_mode` ; mesures `impressions`, `clicks`, `spend`, `conversions`, `conversion_value`, engagement ; KPI `ctr`, `cpc`, `cpa`, `conversion_rate`, `roas` ([définitions](kpi_reference.md)) ; audit `ingested_at`, `extract_run_id`, `mart_created_at`.

`mart_platform_monthly` : `report_month`, `platform`, `data_mode`, `campaigns`, sommes des mesures, KPI recalculés depuis les sommes.

`dim_campaign` : `platform`, `campaign_id`, `current_campaign_name`, `data_mode`, `first_report_date`, `last_report_date`.

## Nommage des jeux de données

`mdp_raw` (unique) ; `mdp_<couche>` en prod (`mdp_staging`, `mdp_intermediate`, `mdp_marts`) ; `<dataset_dev>_<couche>` ailleurs (défaut `mdp_dev_marts`). Voir la macro `generate_schema_name`.

## Partitionnement et coût

Raw et `mart_campaign_daily` sont partitionnées par jour ; les requêtes de BI doivent filtrer sur `report_date`. Le remplacement de fenêtre du chargement filtre la colonne de partition : seules les partitions concernées sont lues.
