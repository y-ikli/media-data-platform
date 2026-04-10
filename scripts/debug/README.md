# Scripts de diagnostic

Scripts utilitaires pour diagnostiquer les problèmes de connexion et d'ingestion BigQuery.
Ces scripts ne font pas partie du pipeline — ils servent uniquement au troubleshooting.

---

## Problèmes couverts

| Symptôme | Script à lancer |
|----------|----------------|
| Connexion BigQuery impossible | `test_bigquery.py` |
| Tables vides après ingestion | `diagnose_bigquery.sh` |
| Vérification rapide de l'état | `verify_bigquery.sh` |
| Valider les dépendances Python + connecteurs | `test_bigquery_integration.sh` |

---

## Scripts

### `test_bigquery.py` — Test de connexion

Vérifie que les credentials GCP sont valides et que la connexion BigQuery fonctionne.

```bash
# Depuis la racine du projet
python scripts/debug/test_bigquery.py
python scripts/debug/test_bigquery.py --datasets   # liste aussi les datasets
```

Utile quand : token expiré, mauvais chemin de clé, projet GCP incorrect.

---

### `diagnose_bigquery.sh` — Diagnostic complet

Parcourt toutes les étapes dans l'ordre : credentials → connexion → datasets → tables → données.
Chaque étape affiche une solution si elle échoue.

```bash
bash scripts/debug/diagnose_bigquery.sh
```

Utile quand : les tables existent mais sont vides, ou le pipeline a échoué sans message clair.

**Causes fréquentes de tables vides :**
- Facturation GCP désactivée → expiration des partitions à 60 jours (sandbox)
- `WRITE_TRUNCATE` sur la table entière au lieu d'une partition
- Token Meta Ads expiré pendant l'ingestion

---

### `verify_bigquery.sh` — Vérification rapide

Affiche l'état des datasets et le nombre de lignes dans chaque table.

```bash
bash scripts/debug/verify_bigquery.sh
```

Utile quand : vérifier rapidement après une ingestion que les données sont bien là.

---

### `test_bigquery_integration.sh` — Validation des dépendances

Vérifie que toutes les dépendances Python sont installées et que les connecteurs s'importent correctement.

```bash
bash scripts/debug/test_bigquery_integration.sh
```

Utile quand : après `uv sync` ou changement d'environnement, avant de lancer le pipeline.

---

## Ordre recommandé en cas de problème

```
1. python scripts/debug/test_bigquery.py
   → Si KO : vérifier GOOGLE_APPLICATION_CREDENTIALS dans .env

2. bash scripts/debug/verify_bigquery.sh
   → Affiche l'état actuel des tables

3. bash scripts/debug/diagnose_bigquery.sh
   → Diagnostic détaillé avec solutions

4. bash scripts/debug/test_bigquery_integration.sh
   → Si les imports Python échouent
```

---

## Problème billing (sandbox BigQuery)

Si les tables restent vides malgré des logs d'ingestion positifs :

```bash
# Vérifier l'expiration des datasets
bq show --format=prettyjson media-data-platform:mdp_raw | grep -E "expiration|Expiration"
```

Si `defaultPartitionExpirationMs` est à `5184000000` (60 jours) et que la facturation
n'est pas activée, toutes les données historiques expirent immédiatement.

**Solution :** activer la facturation GCP, puis :

```bash
bq update --default_partition_expiration=0 --default_table_expiration=0 media-data-platform:mdp_raw
bq update --default_partition_expiration=0 --default_table_expiration=0 media-data-platform:mdp_staging
bq update --default_partition_expiration=0 --default_table_expiration=0 media-data-platform:mdp_intermediate
bq update --default_partition_expiration=0 --default_table_expiration=0 media-data-platform:mdp_marts
```

Puis relancer le pipeline : `bash scripts/run_pipeline.sh`