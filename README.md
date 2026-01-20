# Marketing Data Platform — Data Engineering Project

## Présentation générale

Ce projet implémente une **plateforme data marketing end-to-end**, inspirée des environnements d’agences média opérant à grande échelle.  
Il est conçu comme un **projet portfolio professionnel**, visant à démontrer une maîtrise concrète du **Data Engineering Cloud**, de l’ingestion jusqu’aux data products analytiques.

---

## Contexte métier

Les données marketing proviennent de multiples plateformes externes (Google Ads, Meta Ads, etc.) et de systèmes internes.  
Elles présentent :
- des schémas hétérogènes,
- des définitions de KPI non homogènes,
- des fréquences de mise à jour variables.

Sans plateforme centralisée, les pipelines de reporting deviennent fragiles, coûteux à maintenir et difficiles à faire évoluer.

---

## Problème → Solution → Impact

### Problème
- Multiplicité des sources.
- Absence de standardisation des métriques.
- Ingestions peu industrialisées.
- Couplage fort entre reporting et systèmes sources.

### Solution
Conception et implémentation d’une **plateforme data marketing cloud-ready** reposant sur :
- des pipelines d’ingestion incrémentaux et idempotents,
- une séparation stricte des couches data,
- des transformations SQL-first avec dbt,
- une orchestration centralisée via Airflow,
- des data marts analytiques exposant des KPI standardisés.

### Impact
- Données marketing unifiées, fiables et historisées.
- Réduction de la complexité du reporting.
- Accélération des analyses et de la prise de décision.
- Socle prêt pour des usages avancés (optimisation, activation, IA).

---

## Cas d’usage couverts

- Automatisation du reporting marketing multi-sources.
- Harmonisation des KPI publicitaires.
- Construction de data marts orientés performance média.
- Support aux analyses et produits data futurs.

---

## Architecture cible

### Vue logique (schéma simplifié)

```text
Sources marketing (APIs, fichiers)
        |
        v
Ingestion Python
        |
        v
Raw zone (GCS / BigQuery)
        |
        v
Transformations dbt
        |
        v
Analytics zone (BigQuery)
        |
        v
Reporting / Analyse / Data Products
```

### Principes de conception
- Découplage ingestion / transformation.
- Modélisation analytique orientée SQL.
- Responsabilités claires par couche.
- Développement local, déploiement cloud-compatible.
- Données conçues comme des produits réutilisables.

---

## Modélisation des données

### Couches data
- **Raw** : données sources brutes, historisées, enrichies de métadonnées d’ingestion.
- **Staging** : nettoyage, typage et standardisation des schémas.
- **Intermediate** : enrichissements et jointures inter-sources.
- **Marts** : tables métier prêtes pour l’analyse et la BI.

### Grain analytique
- 1 ligne = **campaign × date × plateforme**.

### KPI exposés
- Impressions  
- Clicks  
- Spend  
- Conversions  
- CTR  
- CPA  
- ROAS  

---

## Stack technique

### Langages
- Python
- SQL (BigQuery)

### Cloud & data
- Google Cloud Platform  
  - BigQuery (data warehouse)
  - Google Cloud Storage (zone raw)
- dbt (transformations, tests, documentation)

### Orchestration & opérations
- Airflow (ordonnancement, monitoring)
- Docker & Docker Compose (environnement reproductible)
- GitHub (versioning et CI légère)

---

## Structure du dépôt

```text
.
├── dags/                 # DAGs Airflow
├── src/
│   ├── ingestion/        # Pipelines d’ingestion
│   ├── common/           # Utilitaires partagés
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   ├── tests/
│   └── macros/
│
├── data/
│   ├── raw/
│   └── samples/
│
├── config/
│   └── settings.example.yaml
│
├── tests/
│   └── unit/
│
├── docs/
│   ├── architecture.md
│   ├── data_model.md
│   └── pipelines.md
│
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Qualité, fiabilité et gouvernance

- Tests dbt : not null, unique, accepted values.
- Contrôles de cohérence et de volumétrie à l’ingestion.
- Séparation claire des responsabilités par couche.
- Architecture préparée pour :
  - data contracts,
  - monitoring avancé,
  - optimisation des coûts et performances.

---

## MVP

### Couvert
- Ingestion multi-sources (Google Ads, Meta Ads) via architecture abstraite (DataSourceConnector).
- Historisation des données brutes avec métadonnées d'ingestion.
- Orchestration via Airflow.
- Environnement reproductible (Docker Compose).

### En cours
- Déploiement BigQuery (infra cloud).
- CI/CD et tests automatisés.

### Complété ✅
- **Partie 1:** Environnement local reproductible (Docker + Airflow)
- **Partie 2:** Design BigQuery (datasets raw/staging/marts)
- **Partie 3:** Ingestion Google Ads → Raw
- **Partie 4:** Ingestion Meta Ads → Raw (multi-sources)
- **Partie 5:** dbt Staging (standardisation des deux sources)
- **Partie 6:** dbt Intermediate (unification cross-source)
- **Partie 7:** dbt Marts (data products avec KPI)

---

## Finalité du projet

Ce dépôt sert de :
- **vitrine technique** pour des rôles en Data Engineering / Analytics Engineering,
- **référence d’architecture** pour une plateforme data marketing,
- **base évolutive** pour des expérimentations futures.

L’accent est mis sur la robustesse, la lisibilité et l’alignement avec les standards industriels.
