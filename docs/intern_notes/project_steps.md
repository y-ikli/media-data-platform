# Implémentation — découpage en parties + indicateurs de réussite

## Partie 0 — Cadrage & conventions (fondations)
**Objectif** : figer le périmètre MVP, les conventions, et ce qui est “done”.

**Livrables**
- `docs/architecture.md` : zones (raw/staging/marts), composants, flux.
- `docs/data_model.md` : datasets BigQuery, conventions de nommage, grain des marts.
- `config/settings.example.yaml` : paramètres (env, projets, datasets, buckets).

**Indicateurs de réussite**
- Une personne externe peut expliquer l’architecture en 2 minutes en lisant `docs/architecture.md`.
- Conventions écrites (naming, partition/clustering, clés) + appliquées dans le repo.
- Le MVP est défini en 5 lignes (sources, marts, KPI, orchestration).

---

## Partie 1 — Environnement local reproductible (dev setup)
**Objectif** : pouvoir exécuter le projet localement de façon fiable.

**Livrables**
- `Dockerfile` + `docker-compose.yaml` (Airflow + DB metadata).
- `requirements.txt` (ou `pyproject.toml`) + scripts de lancement.
- `Makefile` (optionnel) : commandes standardisées.

**Indicateurs de réussite**
- `docker compose up -d` démarre Airflow (UI accessible).
- Un DAG “hello” s’exécute et apparaît **Success** dans l’UI.
- Un nouveau clone du repo peut lancer l’environnement en < 15 minutes.

---

## Partie 2 — Design BigQuery & zones de données
**Objectif** : préparer le stockage analytique (datasets, conventions, stratégie perf).

**Livrables**
- Datasets : `mdp_raw`, `mdp_staging`, `mdp_marts`.
- Conventions tables : `raw_<source>__<entity>`, `stg_<source>__<entity>`, `mart_<domain>_<grain>`.
- Choix partition/clustering documentés (par date, source, etc.).

**Indicateurs de réussite**
- Les datasets existent et sont accessibles avec droits minimum.
- Chaque table cible a un grain défini (ex: campaign_id × date × platform).
- Partitionnement défini pour les tables “daily” (marts) et stratégie raw (ingested_at / date).

---

## Partie 3 — Ingestion Source #1 → Raw historisé (pipeline minimal)
**Objectif** : produire une ingestion incrémentale idempotente pour 1 source.

**Livrables**
- `src/ingestion/<source>/extract.py` : extraction (API réelle ou mock).
- `src/ingestion/<source>/load_raw.py` : écriture raw + metadata.
- Schéma raw + table BigQuery (ou fichiers GCS + chargement).
- Données d’exemple dans `data/samples/`.

**Indicateurs de réussite**
- Relancer la même ingestion ne duplique pas les données (idempotence).
- La raw contient `ingested_at`, `source`, `extract_run_id`.
- Les volumes attendus sont cohérents (ex: nb lignes > 0, pas de chute brutale).

---

## Partie 4 — Ingestion Source #2 → Raw (multi-sources)
**Objectif** : prouver la capacité multi-sources (même pattern, autre schéma).

**Livrables**
- Second connecteur dans `src/ingestion/<source2>/`.
- Normalisation des métadonnées d’ingestion (même format que source #1).

**Indicateurs de réussite**
- Deux sources chargent en raw avec la même structure d’ops (logs, run_id, watermark).
- Les run IDs sont traçables et permettent de relier un run à ses outputs.

---

## Partie 5 — dbt Staging (standardisation)
**Objectif** : passer de raw hétérogène à un schéma standard.

**Livrables**
- `dbt/models/staging/` : `stg_<source>__campaign_daily` (ou équivalent).
- Typage, renommage, règles de null-handling.
- Tests dbt : `not_null`, `unique` (sur clés), `accepted_values`.

**Indicateurs de réussite**
- `dbt run` + `dbt test` réussissent sans erreurs.
- Les colonnes critiques sont non-nulles (clés, date, metrics de base si attendu).
- Les schémas staging des deux sources convergent (mêmes noms de colonnes standard).

---

## Partie 6 — dbt Intermediate (unification cross-source)
**Objectif** : fusionner les sources dans un modèle unifié.

**Livrables**
- `dbt/models/intermediate/int_campaign_daily_unified.sql` (union + harmonisation).
- Mapping “platform” (google_ads/meta_ads) et harmonisation currency / units si besoin.

**Indicateurs de réussite**
- Une table unifiée contient les deux plateformes (contrôle de distribution par platform).
- Les clés sont stables : (date, campaign_id, platform) uniques.
- Le nombre de lignes ≈ somme des staging (moins les exclusions documentées).

---

## Partie 7 — dbt Marts (data product BI-ready)
**Objectif** : exposer des tables métier prêtes dashboard.

**Livrables**
- `dbt/models/marts/mart_campaign_daily.sql`
- KPI dérivés : CTR, CPA, ROAS (safe divide).
- Documentation dbt (descriptions, sources, grain) + `dbt docs`.

**Indicateurs de réussite**
- Le mart a un grain explicite + contrainte d’unicité validée.
- Les KPI dérivés ne produisent pas d’inf/NaN (division par 0 gérée).
- Un exemple de requête BI (Top campaigns, spend, ROAS) donne un résultat cohérent.

---

## Partie 8 — Orchestration Airflow (end-to-end)
**Objectif** : automatiser extract → raw → dbt (run/test) avec observabilité minimale.

**Livrables**
- `dags/marketing_data_platform.py` (DAG principal)
- Tâches : extract/load pour chaque source + `dbt run` + `dbt test`.
- Retries, logs, paramètres (date).

**Indicateurs de réussite**
- Un run Airflow exécute tout le pipeline et finit **Success**.
- En cas d’échec volontaire (ex: API down), Airflow retry + log exploitable.
- Le DAG est idempotent sur une même fenêtre de dates.

---

## Partie 9 — Qualité & contrôles (data + ops)
**Objectif** : ajouter des garde-fous “production-like”.

**Livrables**
- Contrôles volumétrie (ex: seuils min/max) en tâches Airflow ou SQL checks.
- Tests dbt avancés (relationships, freshness si possible).
- Tableau de bord minimal de runs (même via logs + summary table).

**Indicateurs de réussite**
- Un contrôle volumétrie détecte une anomalie (test en cassant un input).
- Les tests dbt échouent quand une règle métier est violée (démo).
- Un run produit un “run summary” (durée, nb lignes, statut) consultable.

---

## Partie 10 — CI légère (crédibilité pro)
**Objectif** : garantir qualité de code + stabilité du repo.

**Livrables**
- GitHub Actions : lint + unit tests + `dbt compile` (ou `dbt parse`).
- `tests/unit/` : quelques tests (par ex: parsing config, mapping schema).

**Indicateurs de réussite**
- Un PR déclenche la CI et passe au vert.
- Un test simple échoue si une régression est introduite (démo).

---

## Partie 11 — Documentation & démonstration (portfolio)
**Objectif** : rendre le projet “lisible” et facilement évalué.

**Livrables**
- README final (install, run, architecture, datasets, KPI).
- `docs/` : architecture + data model + pipelines.
- Captures (Airflow DAG, dbt docs, BigQuery tables) dans `docs/assets/`.

**Indicateurs de réussite**
- Un recruteur peut : cloner → lancer → voir un run Airflow → requêter un mart.
- Screenshots prouvent l’exécution (Airflow Success, dbt docs, tables BQ).

---

## MVP recommandé (pour aller vite mais pro)
- 2 sources (Google Ads + Meta Ads)
- 1 modèle unifié `int_campaign_daily_unified`
- 1 mart principal `mart_campaign_daily`
- Airflow DAG end-to-end + dbt tests essentiels
- 1 CI légère + docs minimales
