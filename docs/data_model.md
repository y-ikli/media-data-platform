# Data Model — Marketing Data Platform

## Vue d'ensemble

La plateforme suit une architecture **médaillons (Medallion)** classique : Raw → Staging → Marts.

```
Google Ads API │ Meta Ads API
     ↓         │     ↓
  Ingestion    │  Ingestion
     ↓         │     ↓
mdp_raw.raw_*__campaign_daily (historisées brutes)
     ↓         │     ↓
mdp_staging.stg_*__campaign_daily (nettoyage + typage)
     ↓         │     ↓
mdp_staging.int_campaign__daily_unified (unification)
     ↓         ↓
mdp_marts.mart_campaign__daily (KPI finalisés)
     ↓
BI / Reporting
```

---

## Datasets BigQuery

### mdp_raw
- **Rôle** : Historisation brute des données sources
- **Accès** : Read-only (populated par ingestion Python)
- **Retention** : Historique complet
- **Tables** : `raw_<source>__<entity>` (ex: `raw_google_ads__campaign_daily`)

### mdp_staging
- **Rôle** : Transformation et unification
- **Contenu** : 
  - Staging tables typées + flagging qualité
  - Intermediate tables (join multi-source)
- **Accès** : Analytics engineering (dbt models)
- **Retention** : Historique complet

### mdp_marts
- **Rôle** : Tables analytiques prêtes pour la BI
- **Accès** : BI tools, dashboards, reporting
- **Retention** : Historique complet
- **Tables** : `mart_<domain>__<grain>` (ex: `mart_campaign__daily`)

---

## Grain analytique (clé métier)

### Définition
**1 ligne = 1 campagne publicitaire × 1 date × 1 plateforme**

### Clé d'unicité
```
PRIMARY KEY (date, platform, campaign_id)
```

### Exemples
```
date       | platform   | campaign_id | campaign_name | impressions | clicks | spend | conversions
2024-01-15 | google_ads | camp_123    | Campaign A    | 1000        | 50     | 250   | 5
2024-01-15 | meta_ads   | camp_456    | Campaign B    | 2000        | 80     | 400   | 8
2024-01-16 | google_ads | camp_123    | Campaign A    | 1100        | 55     | 275   | 6
```

---

## Conventions de nommage

Pour faciliter la navigation, chaque table suit une convention stricte :

| Couche | Format | Exemple | Signification |
|--------|--------|---------|---------------|
| Raw | raw_<source>__<entity> | raw_google_ads__campaign_daily | Brut Google Ads |
| Staging | stg_<source>__<entity> | stg_google_ads__campaign_daily | Google Ads nettoyé |
| Intermediate | int_<domain>__<entity> | int_campaign__daily_unified | Unification multi-sources |
| Marts | mart_<domain>__<grain> | mart_campaign__daily | Table analytique |

---

## Colonnes standard

### Dimensions (identifient la ligne)
- `date` : Date de la campagne (YYYY-MM-DD)
- `platform` : Source (google_ads, meta_ads)
- `account_id` : ID du compte marketing
- `campaign_id` : ID unique campagne
- `campaign_name` : Nom lisible campagne

### Métriques (valeurs agrégées)
- `impressions` : Nombre d'affichages
- `clicks` : Nombre de clics
- `spend` : Dépense en devise source
- `conversions` : Conversions générées

### Métadonnées d'ingestion (Raw uniquement)
- `ingested_at` : Quand la donnée a été chargée
- `extract_run_id` : UUID de la session d'extraction
- `source` : Source système

---

## KPI Calculés (au niveau Marts)

| KPI | Formule | Interprétation |
|-----|---------|------------------|
| CTR | clicks / impressions | % clics vs affichages |
| CPA | spend / conversions | Coût par conversion |
| Conversion Rate | conversions / clicks | % conversions vs clics |

---

## Principes de conception

1. **Idempotence** : Rejouer l'ingestion = même résultat
2. **Historisation** : Aucune donnée supprimée (append-only)
3. **Réconciliation** : extract_run_id pour tracer les batches
4. **Qualité progressive** : Flags au staging, rejets au mart
5. **Séparation** : Raw (brut) → Staging (transformé) → Marts (analytique)
