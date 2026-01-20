# DAG : marketing_data_platform

## Vue d'ensemble

**ID du DAG :** `marketing_data_platform`  
**Schedule :** Quotidien à 2 AM UTC (`0 2 * * *`)  
**Catchup :** Désactivé  
**Propriétaire :** Équipe Platform  
**Tags :** `platform`, `core`, `orchestration`

## Objectif

Orchestration end-to-end du pipeline de la plateforme de données marketing :
- **Extraire** les données brutes depuis les APIs Google Ads et Meta Ads
- **Transformer** les données via les couches dbt (staging → intermediate → marts)
- **Tester** la qualité des données et générer la documentation

## Flux des tâches

```
extract_google_ads ──┐
                      ├──> dbt_run ──> dbt_test ──> dbt_docs_generate ──> pipeline_summary
extract_meta_ads ────┘
```

### Phase 1 : Extraction des données (Parallèle)

| Tâche | Description | Retries | Timeout |
|-------|-------------|---------|---------|
| `extract_google_ads` | Importe campagnes et métriques Google Ads depuis source brute | 2 | 5 min entre |
| `extract_meta_ads` | Importe campagnes et métriques Meta Ads depuis source brute | 2 | 5 min entre |

Les deux tâches s'exécutent **en parallèle** pour maximiser le débit.

**Paramètres** (optionnel, via Configuration de run) :
```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-01-02"
}
```
Défauts : `start_date = "2024-01-01"`, `end_date = "2024-01-02"`

### Phase 2 : Transformations dbt

| Tâche | Description | Retries | Notes |
|-------|-------------|---------|-------|
| `dbt_run` | Exécute modèles dbt dans l'ordre : staging → intermediate → marts | 2 | Full refresh pour idempotence |
| `dbt_test` | Exécute tests dbt (vérifications qualité données) | 1 | S'exécute même si dbt_run échoue via `TriggerRule.ALL_DONE` |
| `dbt_docs_generate` | Génère la documentation dbt | - | S'exécute indépendamment du statut des tests |

### Phase 3 : Résumé & Observabilité

| Tâche | Description |
|-------|-------------|
| `pipeline_summary` | Agrège résultats de toutes les tâches, log le résumé pour monitoring/alertes |

## Gestion des erreurs

### Politique de retries
- **Tâches extraction :** 2 retries avec délai 5 min (max 15 min par tâche)
- **Tâches dbt :** 2 retries (dbt_run), 1 retry (dbt_test)
- **Backoff par défaut :** Intervalle linéaire 5 minutes

### Règles de déclenchement
- **dbt_test :** `ALL_DONE` — s'exécute même si `dbt_run` échoue, pour capturer résultats tests
- **dbt_docs_generate :** `ALL_DONE` — génère docs indépendamment du statut des tâches précédentes
- **pipeline_summary :** `ALL_DONE` — crée toujours un résumé pour monitoring

## Lignage des données

### Entrées
- **Table raw Google Ads :** `mdp_raw.raw_google_ads__campaign_daily`
- **Table raw Meta Ads :** `mdp_raw.raw_meta_ads__campaign_daily`

### Sorties
- **Vues staging :** `mdp_staging.stg_google_ads__campaign_daily`, `mdp_staging.stg_meta_ads__campaign_daily`
- **Vue intermédiaire :** `mdp_intermediate.int_campaign_daily_unified`
- **Table mart :** `mdp_marts.mart_campaign_daily` (prête BI avec KPIs)

## KPIs Produits

| KPI | Formule | Notes |
|-----|---------|-------|
| CTR | clics / impressions | Retourne NULL si impressions = 0 |
| CPA | dépense / conversions | Retourne NULL si conversions = 0 |
| ROAS | conversions / dépense | Retourne NULL si dépense = 0 |
| CPC | dépense / clics | Retourne NULL si clics = 0 |
| Taux conversion | conversions / clics | Retourne NULL si clics = 0 |

Tous les KPIs utilisent `SAFE_DIVIDE()` de BigQuery pour gestion robuste des NULL.

## Monitoring & Alertes

### Métriques clés à monitorer
- **Durée du pipeline :** Runtime typique ~5-10 minutes (peut varier selon volume données)
- **Nb records extraction :** Doit être stable jour après jour (alerte si >50% variance)
- **Échecs tests :** Tout test dbt échouant bloque les déploiements
- **Fraîcheur dbt :** Données récentes dans marts (< 24h)

### Emplacements des logs
- Logs Airflow : `$AIRFLOW_HOME/logs/marketing_data_platform/`
- Logs dbt : `dbt/mdp/logs/`
- Run Summary : Loggé dans les logs des tâches Airflow (niveau INFO)

## Idempotence

Le DAG est **totalement idempotent** :
- Extraction utilise `full_refresh=True` et timestamps (`ingested_at`, `extract_run_id`) pour dédupliquer
- dbt `--full-refresh` assure rebuild correct de tous les modèles
- Réexécuter même fenêtre de dates produit sortie identique

## Exemple : Déclenchement manuel

Via l'interface Airflow :
1. Ouvrir DAG `marketing_data_platform`
2. Cliquer sur **Trigger DAG** (bouton triangle)
3. Dans "Configuration" (JSON), entrer :
   ```json
   {
     "start_date": "2024-02-01",
     "end_date": "2024-02-02"
   }
   ```
4. Cliquer **Trigger**

Sortie attendue : DAG s'exécute et toutes tâches complètent avec statut **Success** en ~5-10 min.

## Dépannage

### dbt_run échoue avec "target directory not found"
- S'assurer que `dbt_project.yml` et `profiles.yml` sont dans `/home/airflow/gcs/data/dbt/mdp/`
- Vérifier permissions des datasets BigQuery

### Tâches extraction time out
- Vérifier connectivité API (politique réseau, credentials)
- Consulter logs tâches Airflow pour erreurs API
- Augmenter `retry_delay_seconds` si rate-limited

### Tests échouent
- Consulter logs tests dbt dans `dbt/mdp/logs/`
- Causes courantes : valeurs NULL, métriques hors-limites, violations unicité
- Corriger données ou mettre à jour seuils tests dans `_models.yml`

## Requêtes & tableaux de bord associés

### Exemple BI : Top 5 campagnes par ROAS
```sql
SELECT
  campaign_name,
  platform,
  SUM(spend) as total_spend,
  SUM(conversions) as total_conversions,
  ROUND(AVG(roas), 4) as avg_roas
FROM mdp_marts.mart_campaign_daily
WHERE report_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY campaign_name, platform
ORDER BY avg_roas DESC
LIMIT 5;
```

---

**Dernière mise à jour :** 2026-01-20  
**Version :** 1.0
