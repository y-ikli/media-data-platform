# Contrôles Volumétrie - Partie 9

## Vue d'ensemble

Les contrôles volumétrie valident que les volumes de données sont conformes aux attentes, détectent les anomalies (variance jour sur jour), et alertent en cas de déviation significative.

## Architecture

### Module `src/monitoring/volume_checks.py`

#### Seuils définis (VOLUME_THRESHOLDS)

| Table | Min. quotidien | Max. quotidien | Max. variance | Description |
|-------|---|---|---|---|
| `mdp_marts.mart_campaign_daily` | 10 | 100k | 50% | KPIs consolidés |
| `mdp_staging.stg_google_ads__campaign_daily` | 5 | 50k | 50% | Google Ads staging |
| `mdp_staging.stg_meta_ads__campaign_daily` | 5 | 50k | 50% | Meta Ads staging |
| `mdp_raw.google_ads_campaign_daily` | 1 | 50k | 70% | Google Ads raw |
| `mdp_raw.meta_ads_campaign_daily` | 1 | 50k | 70% | Meta Ads raw |

#### Fonctions principales

**`get_volume_checks(project_id: str) -> dict`**

Exécute les vérifications volumétrie pour toutes les tables :
- Compte les lignes ingérées aujourd'hui
- Compte les lignes d'hier pour calcul de variance
- Compare contre les seuils (min, max, variance)
- Retourne un dictionnaire avec résultats détaillés

```python
results = get_volume_checks(project_id="data-pipeline-platform-484814")
# Retourne:
{
    "tables_checked": [
        {
            "table": "mdp_marts.mart_campaign_daily",
            "today_count": 156,
            "yesterday_count": 142,
            "variance_percent": 9.86,
            "status": "PASS",
            "issues": []
        }
    ],
    "warnings": [],
    "errors": [],
    "summary": {
        "total_tables": 5,
        "passed": 4,
        "warned": 1,
        "failed": 0,
        "errored": 0,
        "overall_status": "PASS"
    }
}
```

**`format_volume_report(results: dict) -> str`**

Formate les résultats en rapport lisible pour logging :

```
================================================================================
VOLUME CONTROL CHECK REPORT
================================================================================

Overall Status: PASS
Results: 4 PASS, 1 WARN, 0 FAIL, 0 ERROR

Table Details:
--------------------------------------------------------------------------------
✓ mdp_marts.mart_campaign_daily
  Today: 156 records | Yesterday: 142 records | Variance: 9.86%

⚠ mdp_staging.stg_google_ads__campaign_daily
  Today: 148 records | Yesterday: 95 records | Variance: 55.79%
  ⚠ Day-over-day variance (55.79%) exceeds threshold (50%)
```

### Intégration Airflow

#### Tâche `volume_check_task()`

Ajoutée au DAG `marketing_data_platform.py` :

```python
@task(
    task_id="volume_control_check",
    trigger_rule=TriggerRule.ALL_DONE,  # Run même si tâches précédentes échouent
)
def volume_check_task() -> dict:
    """Execute volume control checks..."""
    results = get_volume_checks(project_id=os.getenv("GCP_PROJECT_ID"))
    report = format_volume_report(results)
    logging.info("Volume Check Report:\n%s", report)
    return {
        "status": "completed",
        "overall_status": results["summary"]["overall_status"],
        "summary": results["summary"],
        "report": report,
    }
```

#### Chaîne de dépendances

```
extract_google_ads
                   \
                    } → dbt_run → dbt_test → docs → volume_check ─┐
                   /                                                 |
extract_meta_ads                                                    |
                                                      ┌─ pipeline_summary
```

## Cas de démonstration d'échec

### Cas 1 : Volume sous le minimum (< 10 lignes)

```bash
# Simul : suppression accidentelle de données
gcloud bigquery query --use_legacy_sql=false \
  "DELETE FROM data-pipeline-platform-484814.mdp_marts.mart_campaign_daily 
   WHERE DATE(mart_created_at) = CURRENT_DATE()"

# Résultat du contrôle volumétrie
# ✗ mdp_marts.mart_campaign_daily
#   Today: 0 records | Yesterday: 142 records | Variance: 100.00%
#   ✗ Record count (0) below minimum threshold (10)
# 
# FAIL: mdp_marts.mart_campaign_daily: Below minimum threshold (0/10)
```

### Cas 2 : Variance trop élevée (> 50%)

```bash
# Simul : ingestion massive due à un retry
# Données d'hier : 100 lignes
# Données d'aujourd'hui : 200 lignes (variance = 100%)
# Seuil : 50%

# Résultat du contrôle volumétrie
# ⚠ mdp_marts.mart_campaign_daily
#   Today: 200 records | Yesterday: 100 records | Variance: 100.00%
#   ⚠ Day-over-day variance (100.00%) exceeds threshold (50%)
# 
# WARN: mdp_marts.mart_campaign_daily: High variance detected 
#       (100.00%, yesterday: 100)
```

### Cas 3 : Volume au-delà du maximum (> 100k)

```bash
# Simul : ingestion avec paramètres incorrects
# Résultats : 250 000 lignes

# Résultat du contrôle volumétrie
# ✗ mdp_marts.mart_campaign_daily
#   Today: 250000 records | Yesterday: 142 records | Variance: 176.06%
#   ✗ Record count (250000) exceeds maximum threshold (100000)
# 
# FAIL: mdp_marts.mart_campaign_daily: Exceeds maximum threshold (250000/100000)
```

## Utilisation en production

### Exécution manuelle du contrôle

```python
from src.monitoring.volume_checks import get_volume_checks, format_volume_report

# Récupérer les résultats
results = get_volume_checks(project_id="data-pipeline-platform-484814")

# Afficher le rapport
report = format_volume_report(results)
print(report)

# Accéder aux résultats structurés
print(f"Overall Status: {results['summary']['overall_status']}")
print(f"Warnings: {len(results['warnings'])}")
print(f"Errors: {len(results['errors'])}")
```

### Exécution via Airflow

```bash
# Déclencher le DAG
airflow dags trigger marketing_data_platform

# Voir les résultats de la tâche volume_check
airflow tasks logs marketing_data_platform volume_control_check \
  -e run_id=manual__2026-01-20T12:00:00.000000+00:00
```

### Configuration des alertes

Pour intégrer les alertes Slack (futur) :

```python
if results['summary']['overall_status'] == 'FAIL':
    # Envoyer alerte Slack
    send_slack_alert(
        channel="#data-alerts",
        message=f"Volume check failed: {results['errors']}"
    )
```

## Métriques de qualité

| Métrique | Calcul | Seuil | Impact |
|----------|--------|-------|--------|
| Minimum quotidien | COUNT(*) pour jour courant | Selon table | Critique - détecte perte données |
| Maximum quotidien | COUNT(*) pour jour courant | Selon table | Haute - détecte duplication |
| Variance jour/jour | \|jour_j - jour_j-1\| / jour_j-1 | Selon table (50-70%) | Moyenne - détecte anomalies |

## Prochaines étapes

1. ✅ Ajouter tests dbt avancés
2. ✅ Implémenter contrôles volumétrie en Airflow
3. ⏳ Créer table de summary des runs
4. ⏳ Documenter Partie 9 complètement
