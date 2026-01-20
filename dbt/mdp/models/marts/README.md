# Couche Marts - Plateforme Data Marketing

## Rôle
Contient les data products prêts pour la BI avec KPI calculés et optimisés pour les analyses.

## Modèles

### mart_campaign_daily
Table analytique principale avec métriques et KPI de performance des campagnes.

**Grain:** `report_date` + `campaign_id` + `platform`

**Matérialisation:** TABLE (optimisée pour les requêtes, clustering par report_date + platform)

## KPI Calculés

| KPI | Formule | Description |
|-----|---------|-------------|
| CTR | clicks / impressions | Taux de clic |
| CPA | spend / conversions | Coût par acquisition |
| ROAS | conversions / spend | Retour sur investissement publicitaire |
| CPC | spend / clicks | Coût par clic |
| Conversion Rate | conversions / clicks | Taux de conversion |

**Note:** Tous les KPI utilisent `safe_divide()` pour gérer les divisions par zéro (retourne `null` au lieu de inf/NaN).

## Transformations Appliquées
- Calcul des 5 KPI métier avec division sécurisée
- Ajout du timestamp `mart_created_at` (lineage)
- Clustering pour optimisation des requêtes
- Préservation des métadonnées d'ingestion

## Exemples d'Usage

```sql
-- Top 10 campagnes par dépense
select
  campaign_name,
  platform,
  sum(spend) as total_spend,
  avg(roas) as avg_roas
from mart_campaign_daily
where report_date >= current_date() - 30
group by campaign_name, platform
order by total_spend desc
limit 10;

-- Comparaison entre plateformes
select
  platform,
  count(distinct campaign_id) as nb_campagnes,
  sum(impressions) as total_impressions,
  avg(ctr) as ctr_moyen,
  sum(spend) as depense_totale,
  avg(roas) as roas_moyen
from mart_campaign_daily
where report_date >= current_date() - 7
group by platform;
```

## Lineage
```
stg_google_ads__campaign_daily ─┐
                                ├─► int_campaign_daily_unified ──► mart_campaign_daily
stg_meta_ads__campaign_daily ───┘
```

## Utilisation

```bash
# Exécuter la couche marts
dbt run --select marts

# Tester la couche marts
dbt test --select marts
```

## Notes
- Les schémas détaillés et tests sont dans `_models.yml`
- Pour les définitions complètes des KPI, voir `docs/kpi_reference.md`
- Rafraîchissement quotidien recommandé
dbt test --select marts

# Run specific mart
dbt run --select marts.mart_campaign_daily

# Run full pipeline to marts
dbt run --select +marts
```
