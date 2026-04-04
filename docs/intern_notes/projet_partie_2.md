# Partie 2 — Design BigQuery & zones de données

## Objectif
Définir **clairement et définitivement** la structure de stockage analytique avant toute ingestion :
- datasets BigQuery,
- conventions de nommage,
- grain des tables,
- règles de partitionnement et d’optimisation.

À la fin de cette partie, on sait **où chaque donnée doit vivre** et **sous quelle forme**.

---

## 2.1 — Datasets BigQuery (zones)

### Datasets utilisés

```text
mdp_raw      : données brutes historisées (source de vérité)
mdp_staging  : données nettoyées et standardisées
mdp_marts    : tables métier prêtes pour l’analyse et la BI
```

### Rôle de chaque zone

- **mdp_raw**
  - contient les données telles que reçues des sources
  - aucune logique métier
  - historisation complète
  - traçabilité et rejouabilité

- **mdp_staging**
  - typage correct (DATE, INT, NUMERIC…)
  - renommage des colonnes
  - normalisation des schémas inter-sources

- **mdp_marts**
  - tables analytiques stables
  - KPI calculés
  - grain fixe et documenté
  - point d’entrée BI / analyses

---

## 2.2 — Conventions de nommage

### Tables

```text
Raw        : raw_<source>__<entity>
Staging    : stg_<source>__<entity>
Intermediate : int_<domain>__<entity>
Marts      : mart_<domain>__<grain>
```

### Exemples concrets

```text
raw_google_ads__campaign_daily
stg_meta_ads__campaign_daily
int_marketing__campaign_daily_unified
mart_marketing__campaign_daily
```

---

## 2.3 — Grain analytique (contrat clé)

### Grain principal (MVP)

```text
1 ligne = campaign_id × date × platform
```

### Clé d’unicité

```text
(date, platform, campaign_id)
```

Ce grain :
- permet un reporting journalier standard,
- est compatible multi-plateformes,
- est stable dans le temps.

---

## 2.4 — Schéma cible standard (marketing)

### Colonnes obligatoires (staging / marts)

```text
date            DATE
platform        STRING   -- google_ads | meta_ads
account_id      STRING
campaign_id     STRING
campaign_name   STRING
impressions     INT64
clicks          INT64
spend           NUMERIC
conversions     INT64
```

### Règles générales
- aucune colonne métier critique nullable dans les marts,
- types homogènes entre plateformes,
- valeurs négatives interdites sur les métriques.

---

## 2.5 — KPI et règles de calcul

### KPI de base
- impressions
- clicks
- spend
- conversions

### KPI dérivés (safe)

```text
CTR  = clicks / impressions
CPA  = spend / conversions
ROAS = revenue / spend   (optionnel / mock en MVP)
```

### Règles
- division par zéro protégée (`SAFE_DIVIDE`)
- KPI calculés uniquement en **marts**
- aucune logique KPI en raw ou staging

---

## 2.6 — Partitionnement & optimisation BigQuery

### Tables Raw
- partition : `ingested_at` (TIMESTAMP)
- objectif : ingestion incrémentale + audit

### Tables Staging / Intermediate
- partition : `date`
- objectif : transformations efficaces

### Tables Marts
- partition : `date`
- clustering :
  - `platform`
  - `campaign_id`

---

## 2.7 — Métadonnées techniques (raw)

### Colonnes techniques obligatoires

```text
ingested_at     TIMESTAMP
extract_run_id  STRING
source          STRING
payload         JSON / STRING
```

Ces colonnes garantissent :
- traçabilité complète,
- idempotence,
- possibilité de rejouer un run.

---

## 2.8 — Livrables de la Partie 2

- Datasets BigQuery définis (conceptuellement)
- Conventions de nommage figées
- Grain analytique validé
- Schéma standard marketing documenté
- Règles de partitionnement définies

---

## 2.9 — Indicateurs de réussite (DoD)

```text
- Je peux créer toutes les tables cibles sans ambiguïté
- Le grain est clair et unique
- Les KPI sont définis une seule fois
- Aucun pipeline n’est encore nécessaire pour comprendre le modèle
```

---

## Prochaine étape
👉 **Partie 3 — Ingestion Source #1 → Raw historisé (pipeline minimal)**

On commencera avec **une seule source**, des données **mock**, et un objectif simple :
charger du brut proprement, de manière incrémentale et traçable.
