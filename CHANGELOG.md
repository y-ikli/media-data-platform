# Journal de Modifications — Plateforme Data Marketing

Toutes les modifications notables du projet sont documentées ici.

---

## [Partie 0] Cadrage & conventions - 2026-01-15

### Ajout
- Définition du scope du projet (11 parties)
- Architecture logique: Raw → Staging → Intermediate → Marts
- Structure de dossiers: `dags/`, `dbt/`, `src/`, `docs/`
- Conventions: Python en anglais, Documentation en français
- KPI cibles: CTR, CPA, ROAS, CPC, Conversion Rate

---

## [Partie 1] Environnement local (Docker + Airflow) - 2026-01-15

### Ajout
- `docker-compose.yaml`: Airflow 2.9.3 + PostgreSQL
- `requirements.txt`: dépendances Python complètes
- Airflow UI accessible sur `localhost:8080`
- Configuration Airflow avec home directory `/dags`

### Validation
- DAG `hello_airflow` exécuté avec succès
- Logs générés correctement

---

## [Partie 2] Design BigQuery - 2026-01-16

### Ajout
- Création datasets BigQuery:
  - `mdp_raw`: zone brute (schéma adapté des APIs)
  - `mdp_staging`: zone standardisée
  - `mdp_marts`: zone analytique (data products)
- Tables de raw:
  - `raw_google_ads__campaign_daily`
  - `raw_meta_ads__campaign_daily`

---

## [Partie 3] Ingestion Google Ads → Raw - 2026-01-17

### Ajout
- `src/ingestion/google_ads/`: Module d'ingestion
- Connecteur Google Ads Client Library
- Chargement dans `mdp_raw.raw_google_ads__campaign_daily`
- Données quotidiennes par campagne
- `dags/google_ads_ingestion.py`: DAG orchestration

### Caractéristiques
- Idempotent (remplace les données du jour)
- Gestion d'erreurs + retries
- Logging détaillé par tâche

---

## [Partie 4] Ingestion Meta Ads → Raw - 2026-01-18

### Ajout
- `src/ingestion/meta_ads/`: Module d'ingestion
- Connecteur Meta Marketing API
- Chargement dans `mdp_raw.raw_meta_ads__campaign_daily`
- Même grain: report_date + campaign_id
- `dags/meta_ads_ingestion.py`: DAG orchestration

### Validation
- Deux sources parallèles = préparation pour unification

---

## [Partie 5] dbt Staging (standardisation) - 2026-01-19

### Ajout
- Projet dbt: `/dbt/mdp/` (dbt 1.11.2 + dbt-bigquery)
- Modèles staging:
  - `stg_google_ads__campaign_daily.sql`: Renommage, typage, ajout `platform='google_ads'`
  - `stg_meta_ads__campaign_daily.sql`: Même pattern pour Meta Ads
- Tests qualité:
  - `not_null` sur clés primaires et métriques
  - `accepted_values` sur plateforme
  - `unique_combination_of_columns`
- Documentation complète par modèle

### Validation
- 0 erreurs dbt compile
- 2 modèles, 12 tests définis

---

## [Partie 6] dbt Intermediate (unification) - 2026-01-20

### Ajout
- Modèle `int_campaign_daily_unified.sql`:
  - UNION des deux staging layers
  - Préserve la plateforme pour traçabilité
  - Ajout `unified_at` timestamp (lineage)
- Tests qualité:
  - `not_null` sur clés
  - `accepted_values` sur plateforme (google_ads | meta_ads)
  - `unique_combination_of_columns` sur (report_date, campaign_id, platform)
- Documentation: README + diagramme de dépendance

### Grain garantis
- Unicité: (report_date, campaign_id, platform)
- Pas de doublons cross-platform

---

## [Partie 7] dbt Marts (data products) - 2026-01-20

### Ajout
- Modèle `mart_campaign_daily.sql`:
  - TABLE (pas VIEW) = performance en lecture
  - Clustering: (report_date, platform)
  - 5 KPI calculés avec `safe_divide()`:
    - **CTR** = clicks / impressions → [0, 1]
    - **CPA** = spend / conversions → montant devise
    - **ROAS** = conversions / spend → ratio rentabilité
    - **CPC** = spend / clicks → montant devise
    - **Conversion Rate** = conversions / clicks → [0, 1]
  - Aucune valeur inf/NaN possible

- Tests qualité (20+):
  - `not_null` sur toutes les métriques
  - `accepted_values` sur plateforme
  - `accepted_range` sur KPI (min=0)
  - `unique_combination_of_columns`
  - Récence: ≤7 jours

- Documentation:
  - README: Guide des KPI avec exemples SQL
  - `docs/kpi_reference.md`: Définitions officielles par KPI

### Validation
- 4 modèles compilés (staging + intermediate + marts)
- 49 tests qualité définis
- 0 erreurs, 0 avertissements critiques

---

## [Partie 8] Orchestration Airflow (end-to-end) - 2026-01-20

### Ajout
- DAG principal `dags/marketing_data_platform.py` (schedule `0 2 * * *`, catchup off) orchestrant :
  - Extractions parallèles Google Ads + Meta Ads → raw
  - `dbt_run` (staging → intermediate → marts) puis `dbt_test` (ALL_DONE)
  - Génération `dbt docs` + tâche `pipeline_summary`
- Paramètres run optionnels: `start_date`, `end_date` (ISO). Retries configurés (2 sur extract/dbt_run, 1 sur dbt_test), backoff 5 min.
- Documentation : `dags/README.md`, `docs/dags/marketing_data_platform.md` (FR).
- Script de validation des DAGs : `scripts/validate_dags.py` (4/4 DAGs valides).

### Validation
- Compilation Python OK pour les 4 DAGs (`validate_dags.py`).
- Flux end-to-end prêt à être déclenché depuis l'UI ou la CLI Airflow.
- Idempotence assurée par full refresh (extract + dbt).

---

## [Partie 9] Qualité & Contrôles - 2026-01-20

### Ajout
- **Tests dbt avancés (55 tests total)** :
  - Tests de fraîcheur: warn après 7j, error après 10j (`freshness` sur `mart_campaign_daily`)
  - Tests SQL personnalisés (4 fichiers) :
    - `test_kpi_calculations.sql`: Valide CTR, CPC, CPA
    - `test_no_negative_metrics.sql`: Aucune métrique négative
    - `test_ctr_not_exceeding_100_percent.sql`: CTR ≤ 100%
    - `test_clicks_not_exceeding_impressions.sql`: Clicks ≤ impressions
  - Tests de volumétrie: `at_least_one`, `recency`, `unique_combination_of_columns`

- **Contrôles volumétrie automatisés** :
  - Module Python `src/monitoring/volume_checks.py` (265 lignes)
  - Fonction `get_volume_checks()`: valide 5 tables (raw, staging, marts)
  - Seuils configurables: min (1-10), max (50k-100k), variance jour/jour (50-70%)
  - Tâche Airflow `volume_check_task()` dans DAG principal (trigger rule: ALL_DONE)
  - Rapports formatés avec détection d'anomalies (sous minimum, sur maximum, variance élevée)

- **Table run_summary pour tracking des exécutions** :
  - Schéma BigQuery `mdp_marts.run_summary` (28 colonnes, partitionné par `run_date`, clustered par `dag_id` + `status`)
  - Vue `mdp_marts.vw_recent_runs` (30 derniers jours avec icônes de statut)
  - Module Python `src/monitoring/run_logger.py` (230 lignes)
  - Fonction `log_run_summary()`: logging automatique post-exécution
  - Fonction `get_recent_runs()`: récupération des dernières exécutions
  - Script d'initialisation `scripts/create_run_summary_table.sh`
  - Intégration dans tâche `pipeline_summary` du DAG principal

- **Documentation complète (730+ lignes)** :
  - `docs/intern_notes/partie_9_tests_dbt.md`: Tests dbt avec cas d'échec
  - `docs/intern_notes/partie_9_volume_checks.md`: Contrôles volumétrie
  - `docs/intern_notes/partie_9_run_summary.md`: Table summary et requêtes
  - `docs/intern_notes/partie_9_implementation.md`: Synthèse complète

### Modifié
- DAG `marketing_data_platform.py` enrichi :
  - Import modules monitoring (`volume_checks`, `run_logger`)
  - Tâche `volume_check_task()` ajoutée après `dbt_docs`
  - Tâche `summary_task()` enrichie pour logging BigQuery
  - Calcul statut global: `success`, `partial` (warning/erreur partielle), `failed`
  - Tracking des erreurs (task + message)

- Modèle dbt `dbt/mdp/models/marts/_models.yml` :
  - Config freshness ajoutée
  - Test `at_least_one` pour volumétrie minimale

### Validation
- 4/4 DAGs valides (`scripts/validate_dags.py`)
- 55 tests dbt configurés et documentés
- 5 tables avec contrôles volumétrie actifs
- Table BigQuery `run_summary` prête à l'initialisation

---

## Format
Ce journal suit le format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

### Catégories
- **Ajout**: Nouvelles fonctionnalités
- **Modifié**: Changements dans les fonctionnalités existantes
- **Déprécié**: Fonctionnalités bientôt supprimées
- **Supprimé**: Fonctionnalités retirées
- **Correction**: Corrections de bugs
- **Sécurité**: Mises à jour de sécurité
