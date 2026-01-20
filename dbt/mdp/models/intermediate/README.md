# Couche Intermediate - Plateforme Data Marketing

## Rôle
Unifie les données de plusieurs plateformes publicitaires en un modèle unique pour faciliter les analyses cross-platform.

## Modèles

### int_campaign_daily_unified
Combine les métriques quotidiennes de toutes les plateformes (Google Ads, Meta Ads) via UNION.

**Grain:** `report_date` + `campaign_id` + `platform`

## Transformations Appliquées
- UNION des modèles staging avec schéma cohérent
- Préservation de l'identifiant plateforme (traçabilité)
- Ajout du timestamp `unified_at` (lineage)
- Harmonisation des colonnes entre sources

## Lineage
```
stg_google_ads__campaign_daily ─┐
                                ├─► int_campaign_daily_unified
stg_meta_ads__campaign_daily ───┘
```

## Utilisation

```bash
# Exécuter la couche intermediate
dbt run --select intermediate

# Tester la couche intermediate
dbt test --select intermediate
```

## Notes
- Matérialisé en VIEW (léger, toujours à jour)
- Utilisé comme input pour la couche marts
- Les tests et schémas détaillés sont dans `_models.yml`
