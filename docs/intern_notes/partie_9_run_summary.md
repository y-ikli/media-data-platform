# Table Run Summary - Partie 9

## Vue d'ensemble

La table `mdp_marts.run_summary` enregistre toutes les exécutions du pipeline avec métriques détaillées pour le monitoring, les alertes, et les dashboards analytiques.

## Schéma de table

### Table : `mdp_marts.run_summary`

| Colonne | Type | Description |
|---------|------|-------------|
| `run_id` | STRING | Identifiant unique de l'exécution (Airflow run_id) |
| `dag_id` | STRING | Identifiant du DAG |
| `run_date` | DATE | Date de référence de l'exécution (partition key) |
| `execution_date` | TIMESTAMP | Timestamp de démarrage |
| `start_time` | TIMESTAMP | Heure de début |
| `end_time` | TIMESTAMP | Heure de fin |
| `duration_seconds` | INT64 | Durée totale en secondes |
| `status` | STRING | Statut global : `success`, `failed`, `partial`, `running` |
| **Métriques d'extraction** | | |
| `google_ads_extracted_count` | INT64 | Nombre de lignes extraites (Google Ads) |
| `google_ads_status` | STRING | Statut de l'extraction Google Ads |
| `meta_ads_extracted_count` | INT64 | Nombre de lignes extraites (Meta Ads) |
| `meta_ads_status` | STRING | Statut de l'extraction Meta Ads |
| **Métriques dbt** | | |
| `dbt_run_status` | STRING | Statut du dbt run |
| `dbt_test_status` | STRING | Statut des tests dbt |
| `dbt_test_passed` | INT64 | Nombre de tests réussis |
| `dbt_test_failed` | INT64 | Nombre de tests échoués |
| `dbt_test_warnings` | INT64 | Nombre de tests avec warnings |
| `dbt_docs_generated` | BOOL | Documentation générée (true/false) |
| **Métriques de volumétrie** | | |
| `volume_check_status` | STRING | Statut des contrôles volumétrie |
| `volume_check_tables_checked` | INT64 | Nombre de tables vérifiées |
| `volume_check_tables_passed` | INT64 | Nombre de tables OK |
| `volume_check_tables_warned` | INT64 | Nombre de tables avec warning |
| `volume_check_tables_failed` | INT64 | Nombre de tables en échec |
| **Tracking d'erreurs** | | |
| `error_message` | STRING | Message d'erreur (si échec) |
| `error_task` | STRING | Tâche en erreur |
| **Métadonnées** | | |
| `created_at` | TIMESTAMP | Date de création de l'enregistrement |
| `updated_at` | TIMESTAMP | Date de dernière mise à jour |

**Partitionnement** : `run_date` (journalier)  
**Clustering** : `dag_id`, `status`

### Vue : `mdp_marts.vw_recent_runs`

Vue simplifiée des exécutions des 30 derniers jours avec icônes de statut.

```sql
SELECT
  run_id,
  dag_id,
  run_date,
  status,
  CASE
    WHEN status = 'success' THEN '✓'
    WHEN status = 'failed' THEN '✗'
    WHEN status = 'partial' THEN '⚠'
    ELSE '●'
  END AS status_icon,
  duration_seconds,
  google_ads_status,
  meta_ads_status,
  dbt_test_status,
  volume_check_status
FROM `mdp_marts.run_summary`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY execution_date DESC;
```

## Module Python : `src/monitoring/run_logger.py`

### Fonction `log_run_summary()`

Enregistre une exécution dans BigQuery :

```python
from monitoring.run_logger import log_run_summary

log_run_summary(
    project_id="data-pipeline-platform-484814",
    run_id="manual__2026-01-20T12:00:00.000000+00:00",
    dag_id="marketing_data_platform",
    run_date="2026-01-20",
    execution_date=datetime.utcnow(),
    status="success",
    google_ads_result={"status": "success", "record_count": 148},
    meta_ads_result={"status": "success", "record_count": 89},
    dbt_test_result={"success": True, "output": "18 PASS"},
    dbt_docs_result={"docs_generated": True},
    volume_check_result={
        "overall_status": "PASS",
        "summary": {"passed": 5, "warned": 0, "failed": 0}
    }
)
```

### Fonction `get_recent_runs()`

Récupère les dernières exécutions :

```python
from monitoring.run_logger import get_recent_runs

recent_runs = get_recent_runs(
    project_id="data-pipeline-platform-484814",
    limit=10
)

for run in recent_runs:
    print(f"{run['run_date']} - {run['status']} - {run['duration_seconds']}s")
```

## Intégration Airflow

### Tâche `pipeline_summary`

Modifiée pour logger dans BigQuery après chaque exécution :

```python
@task(
    task_id="pipeline_summary",
    trigger_rule=TriggerRule.ALL_DONE,
)
def summary_task(
    google_ads_result,
    meta_ads_result,
    dbt_test_result,
    dbt_docs_result,
    volume_check_result,
    **context
):
    # Déterminer le statut global
    overall_status = "success"
    if any_failure:
        overall_status = "partial"
    
    # Logger dans BigQuery
    log_run_summary(
        project_id=os.getenv("GCP_PROJECT_ID"),
        run_id=context["run_id"],
        dag_id=context["dag"].dag_id,
        run_date=context["ds"],
        execution_date=context["execution_date"],
        status=overall_status,
        google_ads_result=google_ads_result,
        meta_ads_result=meta_ads_result,
        dbt_test_result=dbt_test_result,
        dbt_docs_result=dbt_docs_result,
        volume_check_result=volume_check_result,
    )
```

## Initialisation

### Script : `scripts/create_run_summary_table.sh`

Crée la table et la vue dans BigQuery :

```bash
cd /home/yikli/Bureau/projets/media-data-platform
./scripts/create_run_summary_table.sh
```

**Résultat attendu** :
```
==========================================
Creating run_summary table in BigQuery
==========================================
Project: data-pipeline-platform-484814
Dataset: mdp_marts
Table: run_summary

Creating table mdp_marts.run_summary...
✓ Table created successfully

Creating view mdp_marts.vw_recent_runs...
✓ View created successfully

==========================================
✓ Setup complete!
==========================================
```

## Requêtes utiles

### 1. Dashboard : Dernières exécutions

```sql
SELECT
  run_date,
  status,
  duration_seconds,
  google_ads_extracted_count + meta_ads_extracted_count AS total_extracted,
  dbt_test_passed,
  dbt_test_failed,
  volume_check_status
FROM `data-pipeline-platform-484814.mdp_marts.vw_recent_runs`
LIMIT 10;
```

### 2. Taux de succès sur 30 jours

```sql
SELECT
  status,
  COUNT(*) AS run_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM `data-pipeline-platform-484814.mdp_marts.run_summary`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY status
ORDER BY run_count DESC;
```

**Résultat attendu** :
```
status    | run_count | percentage
----------|-----------|------------
success   | 25        | 83.33
partial   | 4         | 13.33
failed    | 1         | 3.33
```

### 3. Durée moyenne par statut

```sql
SELECT
  status,
  AVG(duration_seconds) AS avg_duration_sec,
  MIN(duration_seconds) AS min_duration_sec,
  MAX(duration_seconds) AS max_duration_sec
FROM `data-pipeline-platform-484814.mdp_marts.run_summary`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY status;
```

### 4. Trends : Évolution du volume extrait

```sql
SELECT
  run_date,
  google_ads_extracted_count,
  meta_ads_extracted_count,
  google_ads_extracted_count + meta_ads_extracted_count AS total_extracted
FROM `data-pipeline-platform-484814.mdp_marts.run_summary`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY run_date DESC;
```

### 5. Alertes : Runs en échec ou partial

```sql
SELECT
  run_date,
  run_id,
  status,
  error_task,
  error_message,
  duration_seconds
FROM `data-pipeline-platform-484814.mdp_marts.run_summary`
WHERE status IN ('failed', 'partial')
  AND run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY run_date DESC;
```

## Cas d'usage - Démonstration

### Cas 1 : Run réussi complet

```
run_id: manual__2026-01-20T14:00:00.000000+00:00
status: success
duration: 245 seconds
google_ads_status: success (148 records)
meta_ads_status: success (89 records)
dbt_test_status: success (18 PASS, 0 FAIL)
volume_check_status: PASS (5/5 tables)
```

### Cas 2 : Run partiel (extraction échouée)

```
run_id: manual__2026-01-20T15:30:00.000000+00:00
status: partial
duration: 120 seconds
google_ads_status: failed
meta_ads_status: success (89 records)
error_task: extract_google_ads
error_message: API timeout after 60 seconds
```

### Cas 3 : Run avec warning volumétrie

```
run_id: manual__2026-01-20T16:00:00.000000+00:00
status: success
duration: 260 seconds
volume_check_status: WARN (4 PASS, 1 WARN, 0 FAIL)
→ variance élevée détectée (55% > 50% threshold)
```

## Métriques de qualité

| Métrique | Calcul | Seuil cible |
|----------|--------|-------------|
| Taux de succès | COUNT(status='success') / COUNT(*) | > 90% |
| Durée moyenne | AVG(duration_seconds) | < 300 sec (5 min) |
| Taux d'échec volumétrie | COUNT(volume_check_status='FAIL') / COUNT(*) | < 5% |
| Taux d'échec tests dbt | SUM(dbt_test_failed) / SUM(dbt_test_passed + dbt_test_failed) | < 2% |

## Prochaines étapes

1. ✅ Ajouter tests dbt avancés
2. ✅ Implémenter contrôles volumétrie
3. ✅ Créer table summary des runs
4. ⏳ Documenter Partie 9 complètement
