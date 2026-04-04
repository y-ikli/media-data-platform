# Tests dbt Avancés - Partie 9

## Vue d'ensemble

Cette documentation décrit les tests dbt implémentés pour garantir la qualité des données du data platform.

## Tests intégrés dans les modèles YML

### 1. Tests de colonne (Column Tests)

Les tests suivants sont appliqués à chaque colonne pertinente :

- **not_null** : Vérifie que la colonne n'est jamais nulle
- **accepted_values** : Vérifie que la colonne ne contient que des valeurs autorisées
- **accepted_range** : Vérifie que les valeurs numériques restent dans la plage définie (min/max)

### 2. Tests de modèle (Data Tests)

#### Freshness (Fraîcheur des données)
```yaml
freshness:
  warn_after: {count: 7, period: day}    # Alerte si données > 7 jours
  error_after: {count: 10, period: day}  # Erreur si données > 10 jours
```

**Objectif** : Garantir que les données du mart ne sont pas stales. Les données doivent être mises à jour au moins tous les 7 jours.

**Démo d'échec** : Si le DAG orchestration n'a pas tourné depuis 10 jours, le test de fraîcheur échouera.

#### Unique Combination
```yaml
- dbt_utils.unique_combination_of_columns:
    arguments:
      combination_of_columns:
        - report_date
        - campaign_id
        - platform
```

**Objectif** : Garantir qu'il y a exactement une ligne par (date, campaign, platform). Prévient les doublons.

**Démo d'échec** : Si une ligne est ingestée deux fois, ce test détectera le doublon.

#### Recency
```yaml
- dbt_utils.recency:
    arguments:
      datepart: day
      interval: 7
```

**Objectif** : Vérifie qu'il y a au moins une ligne avec `report_date` dans les 7 derniers jours.

#### Volume Check
```yaml
- dbt_utils.at_least_one
```

**Objectif** : Garantit que le modèle n'est pas vide (au moins 1 ligne).

---

## Tests SQL avancés (tests/)

Ces tests vérifient la logique métier et l'intégrité des données.

### 1. `test_kpi_calculations.sql`

**Objectif** : Valide que les calculs de KPI sont mathématiquement corrects.

**Règles testées** :
- CTR = clicks / impressions (ou NULL si impressions = 0)
- CPC = spend / clicks (ou NULL si clicks = 0)
- CPA = spend / conversions (ou NULL si conversions = 0)

**Démo d'échec** :
```sql
-- Si un calcul de KPI est corrupt, le test retourne une ligne
SELECT * FROM mart_campaign_daily
WHERE ABS(SAFE_DIVIDE(clicks, impressions) - ctr) > 0.0001
```

### 2. `test_no_negative_metrics.sql`

**Objectif** : Garantit qu'aucune métrique de performance n'est négative.

**Règles testées** :
- `impressions >= 0`
- `clicks >= 0`
- `spend >= 0`
- `conversions >= 0`

**Démo d'échec** :
```sql
-- Cas : extraction avec valeurs négatives
UPDATE mdp_raw.google_ads_campaign_daily
SET impressions = -100
WHERE campaign_id = 'test'
-- → test échouera
```

### 3. `test_ctr_not_exceeding_100_percent.sql`

**Objectif** : Vérifie que CTR ≤ 100%.

**Logique** : Si CTR > 1.0, cela signifie une corruption de données ou un calcul erroné.

**Démo d'échec** :
```sql
-- Cas : clicks > impressions (impossible logiquement)
SELECT * FROM mart_campaign_daily WHERE ctr > 1.0
```

### 4. `test_clicks_not_exceeding_impressions.sql`

**Objectif** : Valide la contrainte logique : clicks ≤ impressions.

**Démo d'échec** :
```sql
-- Un click sans impression = violation de contrainte métier
SELECT * FROM mart_campaign_daily WHERE clicks > impressions
```

---

## Exécution des tests

### Exécuter tous les tests
```bash
cd dbt/mdp
dbt test
```

### Exécuter tests spécifiques
```bash
# Tests du modèle mart_campaign_daily
dbt test --select mart_campaign_daily

# Tests SQL uniquement
dbt test --select test_kpi_calculations

# Tests YML uniquement
dbt test --select mart_campaign_daily --test-type built-in
```

### Résultat attendu
```
Running with dbt 1.7.0
Found 12 models, 18 tests

Executing test: not_null_mart_campaign_daily_report_date
Executing test: not_null_mart_campaign_daily_campaign_id
...
Executing test: test_kpi_calculations
Executing test: test_no_negative_metrics
...

PASS (18 passing tests)
```

---

## Intégration avec Airflow (DAG)

Le DAG `marketing_data_platform.py` exécute les tests via la tâche `dbt_test_task()` :

```python
@task
def dbt_test_task() -> dict[str, Any]:
    """Exécute les tests dbt et retourne les résultats."""
    result = subprocess.run(
        ["dbt", "test"],
        cwd=dbt_project_dir,
        capture_output=True,
        text=True,
        timeout=300
    )
    return {
        "exit_code": result.returncode,
        "success": result.returncode == 0,
        "output": result.stdout + result.stderr
    }
```

**Comportement** :
- Si tous les tests passent : le DAG continue vers les tâches suivantes ✅
- Si un test échoue : une alerte est générée, mais le DAG ne cascade pas (trigger_rule=ALL_DONE) ⚠️

---

## Cas de test - Démonstration d'échec

### Cas 1 : Insérer un doublon (viole unique_combination_of_columns)

```sql
-- Dans BigQuery
INSERT INTO mdp_marts.mart_campaign_daily
SELECT * FROM mdp_marts.mart_campaign_daily
WHERE report_date = CURRENT_DATE()
LIMIT 1;

-- Résultat du test
-- FAIL (1 record): unique_combination_of_columns_mart_campaign_daily
```

### Cas 2 : Modifier une métrique pour violer CTR > 100%

```sql
-- Scenario : clicks > impressions
UPDATE mdp_marts.mart_campaign_daily
SET clicks = 1000, impressions = 100
WHERE campaign_id = 'test'
AND report_date = CURRENT_DATE();

-- Résultat du test
-- FAIL: test_ctr_not_exceeding_100_percent
```

### Cas 3 : Données stales (viole freshness)

```bash
# Cas : dbt test exécuté sans MAJ depuis 11 jours
dbt test

# Résultat
# WARN: Freshness check failed: mart_campaign_daily is 11 days old
# ERROR: error_after threshold (10 days) exceeded
```

---

## Métriques de qualité

| Test | Fréquence | Impact |
|------|-----------|--------|
| Uniqueness (date + campaign + platform) | À chaque dbt test | Critique - prévient les doublons |
| No negative metrics | À chaque dbt test | Critique - détecte corruption |
| KPI calculations | À chaque dbt test | Haute - valide les analyses |
| CTR ≤ 100% | À chaque dbt test | Haute - détecte incohérence |
| Freshness (≤7 jours) | À chaque DAG run | Moyenne - alerte données stales |
| Recency (derniers 7 jours) | À chaque dbt test | Moyenne - détecte gaps de données |

---

## Prochaines étapes

1. ✅ Ajouter tests dbt avancés (relationships, freshness)
2. ⏳ Implémenter contrôles volumétrie en Airflow
3. ⏳ Créer table de summary des runs
4. ⏳ Documenter Partie 9 complètement
