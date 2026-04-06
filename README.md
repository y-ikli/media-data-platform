# Marketing Data Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![dbt 1.7+](https://img.shields.io/badge/dbt-1.7+-orange.svg)](https://docs.getdbt.com/)
[![Airflow 2.9+](https://img.shields.io/badge/Airflow-2.9+-green.svg)](https://airflow.apache.org/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Cloud-red.svg)](https://cloud.google.com/bigquery)

> **Projet en cours d'amélioration** — refactorisation active du code, connexion à la vraie API Meta Ads et alignement de la documentation. Certaines parties peuvent être incomplètes ou en transition.

Pipeline de données marketing end-to-end centralisant les données publicitaires multi-sources (Google Ads, Meta Ads) vers des data marts analytiques dans Google BigQuery.

---

## État des sources de données

| Source | Mode | Détail |
|--------|------|--------|
| **Meta Ads** | Réelle | Connectée à un vrai compte publicitaire via l'API Marketing Meta — campagnes historiques réelles ingérées dans BigQuery |
| **Google Ads** | Simulation | Données générées (pas de compte Google Ads actif) — le connecteur est prêt pour une vraie connexion |

---

## Problème adressé

Les équipes marketing opèrent sur plusieurs plateformes publicitaires en parallèle. Chaque plateforme expose ses propres schémas, ses propres noms de métriques et ses propres définitions de KPI — rendant toute comparaison cross-platform impossible sans traitement préalable.

Ce projet construit le socle de données qui résout ce problème : une chaîne d'ingestion, de transformation et de validation qui produit une table analytique unique, cohérente et fiable, quelle que soit la source.

---

## Architecture

```
Google Ads API        Meta Ads API
      │                     │
      ▼                     ▼
  Connecteur Python    Connecteur Python
      │                     │
      └──────────┬──────────┘
                 ▼
        mdp_raw (BigQuery)
        Données brutes + métadonnées d'ingestion
                 │
                 ▼
        dbt Transformations
        ├─► Staging       — typage, nettoyage, standardisation par source
        ├─► Intermediate  — unification des schémas multi-sources
        └─► Marts         — KPI calculés, partitionnés, prêts pour la BI
                 │
                 ▼
        Dashboards / Analyses ad-hoc
```

---

## Compétences illustrées

### Modélisation BigQuery

4 datasets distincts avec des responsabilités claires :

| Dataset | Rôle | Matérialisation |
|---------|------|-----------------|
| `mdp_raw` | Données brutes, append-only, audit complet | Table partitionnée par date |
| `mdp_staging` | Standardisation par source, flags de qualité | Vue dbt |
| `mdp_intermediate` | Union des sources, schéma commun | Vue dbt |
| `mdp_marts` | KPI finaux, optimisés pour la lecture | Table partitionnée + clusterisée |

La table `mart_campaign_daily` est partitionnée par `report_date` et clusterisée par `platform` et `campaign_id` — choix justifié par les patterns de requêtes analytiques (filtre temporel + filtre par source).

---

### Ingestion Python — pattern extensible

Tous les connecteurs héritent d'une classe abstraite commune `DataSourceConnector` qui impose l'interface et mutualise la logique de chargement :

```
DataSourceConnector (abstract)
├── extract()         ← implémenté par chaque source
├── load_raw()        ← enrichissement metadata (ingested_at, extract_run_id)
└── write_to_bigquery() ← chargement générique
```

Ajouter une nouvelle source (TikTok, LinkedIn...) ne nécessite d'implémenter que la méthode `extract()` — le reste est hérité.

Chaque run génère un `extract_run_id` unique (UUID) permettant de tracer exactement quelle exécution a produit quelle ligne en base.

---

### Transformations dbt

Les KPI sont calculés une seule fois, de façon identique quelle que soit la source :

| KPI | Formule |
|-----|---------|
| CTR | `clicks / impressions` |
| CPA | `spend / conversions` |
| ROAS | `conversions / spend` |
| CPC | `spend / clicks` |
| Taux de conversion | `conversions / clicks` |

Toutes les divisions utilisent `SAFE_DIVIDE` pour éviter les erreurs sur valeurs nulles ou zéro.

Le grain analytique est stabilisé à **1 ligne = 1 campagne × 1 date × 1 plateforme**.

---

### Orchestration Airflow

Le DAG principal `marketing_data_platform` s'exécute quotidiennement à 2h UTC :

```
extract_google_ads ──┐
                     ├──► dbt_run ──► dbt_test ──► volume_control ──► pipeline_summary
extract_meta_ads  ───┘
```

- Les deux extractions sont **parallèles**
- Chaque tâche a une logique de **retry** (2 tentatives, backoff 5 min)
- `pipeline_summary` s'exécute **toujours** (même en cas d'échec partiel) pour logguer l'état complet du run

---

### Qualité des données

Trois niveaux de contrôle :

1. **Tests dbt** à chaque couche — not_null, unicité, plages acceptées, fraîcheur (≤ 7 jours)
2. **Contrôles de volumétrie** — 5 tables surveillées avec seuils min/max et détection de variance jour/jour
3. **Table `run_summary`** — chaque exécution écrit un enregistrement dans BigQuery avec le statut de chaque étape, les comptages et les erreurs éventuelles

---

### CI/CD

GitHub Actions déclenché à chaque push :

- Lint Python (`pylint`)
- Tests unitaires (`pytest`, 17 tests)
- Validation syntaxique des DAGs
- Compilation et parsing dbt

---

## Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Ingestion | Python | 3.11+ |
| Orchestration | Apache Airflow | 2.9.3 |
| Transformation | dbt | 1.7+ |
| Data Warehouse | Google BigQuery | — |
| Tests | pytest + dbt tests | — |
| CI/CD | GitHub Actions | — |

---

## Structure du projet

```
.
├── dags/                    # DAGs Airflow
├── src/
│   ├── ingestion/           # Connecteurs Google Ads et Meta Ads
│   ├── fake_apis/           # Données mock pour le développement local
│   └── monitoring/          # Contrôles volumétrie + logging d'exécution
├── dbt/mdp/
│   └── models/
│       ├── staging/
│       ├── intermediate/
│       └── marts/
├── tests/unit/
├── .github/workflows/
└── docs/                    # Architecture, modèle de données, référence KPI
```

---

## Documentation

| Document | Contenu |
|----------|---------|
| [Architecture](docs/architecture.md) | Flux de données, composants, principes de conception |
| [Modèle de données](docs/data_model.md) | Schémas, grain, partitionnement, clustering |
| [Référence KPI](docs/kpi_reference.md) | Définitions et formules CTR, CPA, ROAS, CPC |

---

## Licence

Apache License 2.0
