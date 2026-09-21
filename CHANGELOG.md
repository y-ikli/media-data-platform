# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/).

## [0.3.0] — Infrastructure GCP en code

### Ajouté
- `infra/` (Terraform) : jeux de données BigQuery, cinq comptes de service à moindre privilège, Secret Manager (conteneurs seulement), Artifact Registry, jobs Cloud Run (ingestion Meta, ingestion Google, dbt), workflow Workflows, Cloud Scheduler, Workload Identity Federation restreinte au dépôt et à la branche, alertes Cloud Monitoring, budget optionnel. ADR-0004 et ADR-0005.
- `Dockerfile` (image unique des jobs, utilisateur non-root) ; workflows GitHub *Infra* (fmt, validate, tflint, trivy) et *Deploy* (WIF).
- `mdp-ingest --lookback-days N` : fenêtre glissante pour les exécutions planifiées.
- `tests/unit/test_infra_contract.py` : arguments des jobs, variables d'environnement, absence de secret dans Terraform.

### Corrigé
- Le chargeur créait le jeu de données raw sans jamais le vérifier ; il le lit d'abord et ne le crée que s'il manque (le compte de production n'a pas le droit de création).

### Non fait
- L'infrastructure n'a pas été appliquée sur un projet GCP réel.

## [0.2.0] — Fiabilisation du pipeline

### Corrigé
- **Chargement non idempotent** : le code faisait `WRITE_APPEND` alors que la documentation annonçait `WRITE_TRUNCATE`. Remplacé par un remplacement atomique de fenêtre ([ADR-0001](docs/adr/0001-chargement-idempotent.md)).
- **ROAS erroné** : la colonne contenait `conversions / dépense`. Désormais `valeur de conversion / dépense` ; colonne `conversion_value` ajoutée. **Changement cassant pour les tableaux de bord qui lisaient l'ancien `roas`.**
- CI qui ne pouvait pas échouer (`dbt compile || echo`) : remplacée par des tests dbt réels sur DuckDB.
- Extraction Google Ads « réelle » qui retournait une liste vide en silence : échoue explicitement.
- Repli silencieux vers des données simulées quand les identifiants manquaient : supprimé.
- Documentation décrivant des DAGs Airflow supprimés depuis avril.

### Ajouté
- Package `mdp` (`src/mdp`), CLI `mdp-ingest` (`--mode`, `--dry-run`, découpage en fenêtres).
- Schémas raw explicites, validation avant chargement, colonne `data_mode`.
- Générateur de données simulées déterministe.
- dbt : déduplication en staging, `mart_campaign_daily` incrémental partitionné, `mart_platform_monthly`, `dim_campaign`, sources avec fraîcheur, tests unitaires dbt, macros portables BigQuery/DuckDB.
- Séparation des environnements (`duckdb`, `dev`, `prod`), authentification par Application Default Credentials.
- Tests : 54 tests Python (couverture 97 %), scénario incrémental complet sur DuckDB, sqlfluff.
- Documentation : architecture, modèle de données, KPI, exploitation, ADR.

### Supprimé
- Scripts shell de diagnostic BigQuery, `deduplicate_raw.py`, modules de monitoring hérités d'Airflow (non utilisés, non testés).

## Historique antérieur (avant 0.2.0)

## [Partie 11] Refactoring — suppression Airflow, nettoyage complet - 2026-04-10

### Supprimé
- `dags/` — DAGs Airflow retirés du projet
- `docker-compose.yaml`, `Dockerfile`, `requirements.txt` — infrastructure Airflow supprimée
- `logs/`, `plugins/` — répertoires générés par Airflow
- `scripts/validate_dags.py`, `scripts/create_run_summary_table.sh`
- `docs/dags/` — documentation DAGs
- `tests/unit/test_dags.py`, `test_run_logger.py`, `test_volume_checks.py`
- Fichiers config obsolètes : `config/settings.example.yaml`, `config/real_api_settings.example.yaml`

### Modifié
- `README.md` — réécrit : focus pipeline ELT sans Airflow, mention production
- `QUICKSTART.md` — réécrit : guide simplifié en 5 étapes
- `.env.example` — suppression variable `AIRFLOW_UID`
- `.github/workflows/ci.yml` — suppression étape `validate_dags`, mise à jour dbt 1.11.1
- `src/ingestion/base.py` — `WRITE_APPEND` → `WRITE_TRUNCATE` par partition (idempotent)
- `dbt/mdp/models/` — suppression syntaxe `arguments:` incompatible avec dbt 1.8

### Rationnel
Airflow est surdimensionné pour un projet d'analyse de campagnes historiques terminées.
Le pipeline ELT est exécuté une seule fois pour charger les données de la période couverte.
En production avec des campagnes actives et continues, Airflow orchestrerait ce pipeline
quotidiennement — l'architecture src/ et dbt/ est conçue pour le supporter sans modification.

---

## [Partie 10] CI légère (crédibilité pro) - 2026-01-20

### Ajout
- GitHub Actions CI : lint pylint + tests unitaires pytest + validation dbt (compile + parse)
- 17 tests unitaires : structure dbt, fake APIs, run logger, volume checks

---

## [Partie 9] Qualité & Contrôles - 2026-01-20

### Ajout
- 36 tests dbt : not_null, accepted_values, unique_combination_of_columns, 4 tests SQL personnalisés
- Module `src/monitoring/volume_checks.py` : contrôles volumétrie 5 tables
- Module `src/monitoring/run_logger.py` : logging des runs dans BigQuery

---

## [Partie 8] Orchestration Airflow (end-to-end) - 2026-01-20

### Ajout
- DAG `marketing_data_platform` : extract parallèle → dbt run → dbt test → volume check → summary
- DAGs standalone : `meta_ads_ingestion_raw`, `google_ads_ingestion_raw`
- Params Airflow : `start_date`, `end_date` pré-remplis dans le formulaire de trigger

> Note : Airflow retiré en Partie 11. L'architecture reste compatible pour une réintégration.

---

## [Partie 7] dbt Marts - 2026-01-20

### Ajout
- `mart_campaign_daily` : table finale, KPI calculés avec SAFE_DIVIDE (CTR, CPC, CPA, ROAS, conversion_rate)
- Clustering par (report_date, platform)
- Colonnes engagement Meta : likes, comments, shares, video_views, page_engagement

---

## [Partie 6] dbt Intermediate - 2026-01-20

### Ajout
- `int_campaign_daily_unified` : UNION ALL Google + Meta avec schéma commun
- Cast `campaign_id` en STRING (Google = string, Meta = entier)
- `conversions` null pour Meta (non fourni par l'API)

---

## [Partie 5] dbt Staging - 2026-01-19

### Ajout
- `stg_google_ads__campaign_daily` : renommage, typage, filtre nulls
- `stg_meta_ads__campaign_daily` : même pattern + colonnes engagement spécifiques Meta
- Macro `generate_schema_name` : évite la concaténation `mdp_staging_staging`

---

## [Partie 4] Connexion API Meta réelle - 2026-04-09

### Ajout
- Connecteur Meta Ads via SDK `facebook-business`
- Extraction insights : impressions, clicks, spend, likes, comments, shares, video_views
- Aplatissement des `actions` Meta (liste de dicts → colonnes individuelles)
- Script `scripts/ingest_meta_ads.py` avec `--start`, `--end`, `--fake`
- Limite API Meta : 37 mois max en arrière

### Données ingérées
- 447 lignes, 46 campagnes, $1 402.49 spend, période 2023-04-23 → 2025-08-25

---

## [Partie 3] Ingestion Google Ads (simulation) - 2026-01-17

### Ajout
- `src/ingestion/google_ads/` : connecteur fake API
- `src/fake_apis/` : générateur de données simulées (5 campagnes fictives)
- Pattern Strategy : même interface que la vraie API (prêt pour connexion réelle)

---

## [Partie 2] Design BigQuery - 2026-01-16

### Ajout
- 4 datasets : `mdp_raw`, `mdp_staging`, `mdp_intermediate`, `mdp_marts`
- Classe abstraite `DataSourceConnector` : extract → load_raw → write_to_bigquery
- Métadonnées d'ingestion : `ingested_at`, `extract_run_id` (UUID), `source`

---

## [Partie 1] Setup projet - 2026-01-15

### Ajout
- Structure dossiers : `src/`, `dbt/`, `scripts/`, `docs/`, `tests/`
- `pyproject.toml` : dépendances locales (uv, Python 3.13)
- Conventions : code en anglais, documentation en français

---

## [Partie 0] Cadrage - 2026-01-15

### Ajout
- Scope : pipeline ELT marketing multi-sources → BigQuery → BI
- Architecture Medallion : Raw → Staging → Intermediate → Marts
- KPI cibles : CTR, CPA, ROAS, CPC, Conversion Rate
