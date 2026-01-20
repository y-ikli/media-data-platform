# Couche Staging - Plateforme Data Marketing

## Rôle
Standardise les données brutes des plateformes publicitaires en schémas cohérents et typés.

## Modèles

### stg_google_ads__campaign_daily
Métriques quotidiennes de campagne Google Ads

**Grain:** `report_date` + `campaign_id`

### stg_meta_ads__campaign_daily
Métriques quotidiennes de campagne Meta Ads (Facebook/Instagram)

**Grain:** `report_date` + `campaign_id`

## Transformations Appliquées
- Nommage standardisé des colonnes
- Typage correct des données (INT64 pour compteurs, NUMERIC pour dépenses)
- Filtrage des valeurs nulles sur les clés requises
- Ajout de la colonne `platform` (identification de la source)
- Préservation des métadonnées d'ingestion (timestamps, run IDs)

## Lineage
```
raw_google_ads__campaign_daily ──► stg_google_ads__campaign_daily ──┐
                                                                     ├─► int_campaign_daily_unified
raw_meta_ads__campaign_daily ───► stg_meta_ads__campaign_daily ────┘
```

## Utilisation

```bash
# Exécuter tous les modèles staging
dbt run --select staging

# Exécuter une plateforme spécifique
dbt run --select staging.google_ads
dbt run --select staging.meta_ads

# Tester la couche staging
dbt test --select staging
```

## Notes
- Les schémas détaillés et tests sont dans `_models.yml`
- Base pour la couche intermediate (unification)
