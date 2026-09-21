# Exploitation

## Ingérer

```bash
uv run mdp-ingest --source meta_ads --start 2024-01-01 --end 2024-03-31 --dry-run   # extrait et valide, sans écrire
uv run mdp-ingest --source meta_ads --start 2024-01-01 --end 2024-03-31             # données simulées
uv run mdp-ingest --source meta_ads --mode real --start 2024-01-01 --end 2024-03-31 # API Meta (variables META_ADS_*)
```

Variables : `GCP_PROJECT_ID` (obligatoire hors dry-run), `BQ_LOCATION` (défaut `europe-west1`), `BQ_RAW_DATASET` (défaut `mdp_raw`). Authentification : `gcloud auth application-default login`.

Chaque fenêtre journalise une ligne JSON : source, mode, table, bornes, lignes, `extract_run_id`, durée.

## Rejouer ou corriger une période

L'ingestion est idempotente : relancer la même commande remplace la fenêtre. Après une correction en zone raw, recalculer les marts :

```bash
DBT_TARGET=prod dbt run -s mart_campaign_daily --vars '{reprocess_from: "2024-01-01"}'   # depuis une date
DBT_TARGET=prod dbt run -s mart_campaign_daily --full-refresh                            # tout reconstruire
```

Sans option, l'incrémental retraite les 7 derniers jours (`lookback_days`) avant la date maximale déjà chargée.

## Lire les échecs

| Message | Cause | Action |
|---|---|---|
| `Lot rejeté : … clicks > impressions` | violation du contrat de données à la source | corriger ou exclure la source ; rien n'a été chargé |
| `GCP_PROJECT_ID n'est pas défini` | configuration | voir `.env.example` |
| `Mode real : variables manquantes` | identifiants Meta absents | renseigner `META_ADS_*` |
| `Aucune ligne … fenêtre conservée` | l'API a renvoyé zéro ligne | vérifier la source ; l'historique n'est pas supprimé |

## Développer sans cloud

```bash
make install     # environnement
make dbt-duckdb  # dbt build complet sur DuckDB
make ci          # lint + tests
```
