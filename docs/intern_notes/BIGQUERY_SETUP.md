# Guide d’Intégration BigQuery

## Vue d’ensemble

Ce projet est maintenant **pleinement intégré** avec Google Cloud BigQuery. Les données sont extraites, enrichies et écrites directement dans BigQuery.

### Architecture

```
Fake APIs (Google Ads, Meta Ads)
    ↓
Connecteurs (Python)
    ↓ extract() → load_raw() → write_to_bigquery()
    ↓
Dataset BigQuery Raw (mdp_raw)
    ↓
Transformations dbt
    ↓
BigQuery Marts (mdp_marts)
```

## Démarrage rapide

### Étape 1 : Créer un compte de service GCP

1. Aller sur [Google Cloud Console](https://console.cloud.google.com)
2. Créer un nouveau projet ou sélectionner un existant
3. Aller dans **IAM & Admin** → **Comptes de service**
4. Cliquer sur **Créer un compte de service**
   - Nom : `mdp-airflow`
   - Description : "Connecteur Airflow pour MDP"
5. Cliquer sur **Créer et continuer**
6. Attribuer les rôles :
   - ✓ BigQuery Admin
   - ✓ BigQuery Data Editor
   - ✓ Storage Object Admin
7. Cliquer sur **Continuer** → **Terminer**

### Étape 2 : Créer et télécharger la clé JSON

1. Dans la page des comptes de service, cliquer sur `mdp-airflow`
2. Aller dans l’onglet **Clés**
3. Cliquer sur **Ajouter une clé** → **Créer une nouvelle clé**
4. Choisir **JSON**
5. Un fichier JSON sera téléchargé automatiquement (ex : `mdp-airflow-1234567.json`)
6. Déplacez-le dans votre projet : `mv ~/Downloads/mdp-airflow-*.json ~/votre-projet/gcp-key.json`

### Étape 3 : Définir la variable d’environnement

**Option A : Machine locale**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=~/chemin/vers/gcp-key.json
```

**Option B : Docker Compose**

Modifiez `docker-compose.yaml` :
```yaml
airflow-scheduler:
  environment:
    GOOGLE_APPLICATION_CREDENTIALS: /opt/airflow/gcp-key.json
  volumes:
    - ~/chemin/vers/gcp-key.json:/opt/airflow/gcp-key.json:ro
```

**Option C : Fichier .env**
```bash
cp .env.example .env
# Éditez .env et définissez : GOOGLE_APPLICATION_CREDENTIALS=/opt/airflow/gcp-key.json
```

### Étape 4 : Vérifier l’installation

```bash
bash scripts/setup_bigquery.sh
```

Sortie attendue :
```
✓ Connexion à BigQuery réussie
✓ Project ID: data-pipeline-platform-484814
✓ Dataset 'mdp_raw' existe
✓ Dataset 'mdp_staging' existe
...
✓ Configuration BigQuery terminée !
```

## Lancer l’ingestion avec BigQuery

### Via l’interface Airflow

1. Démarrer Airflow :
   ```bash
   docker-compose up -d
   ```

2. Ouvrir http://localhost:8080 (admin/admin)

3. Déclencher le DAG : `google_ads_ingestion_raw`
   - Config : `{"start_date": "2024-12-01", "end_date": "2024-12-31"}`

4. Vérifier les logs pour la confirmation d’écriture BigQuery :
   ```
   ✓ Successfully loaded 125 rows to mdp_raw.google_ads_campaign_daily
   ```

### Vérifier les données dans BigQuery

```bash
# Interroger les données brutes
bq query --use_legacy_sql=false '
SELECT COUNT(*) as record_count, source, MAX(ingested_at) as latest_ingest
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
GROUP BY source
'

# Voir quelques enregistrements
bq query --use_legacy_sql=false '
SELECT * FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
LIMIT 10
'
```

## Dépannage

### Erreur : "Could not construct grpc object"

**Cause** : `GOOGLE_APPLICATION_CREDENTIALS` non défini ou chemin invalide

**Solution** :
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/chemin/correct/vers/gcp-key.json
echo $GOOGLE_APPLICATION_CREDENTIALS  # Vérifiez que c’est bien défini
```

### Erreur : "Permission denied" dans BigQuery

**Cause** : Le compte de service n’a pas les rôles requis

**Solution** :
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/iam-admin/iam)
2. Trouver le compte de service `mdp-airflow`
3. Modifier les permissions et ajouter :
   - BigQuery Admin
   - BigQuery Data Editor

### Erreur : "Dataset not found"

**Cause** : Le dataset `mdp_raw` n’existe pas

**Solution** :
```bash
bash scripts/setup_bigquery.sh
```

Cela créera tous les datasets nécessaires.

### Erreur : "Table already exists"

**Cause** : Normal lors d’un second lancement (les données sont ajoutées, pas écrasées)

**Vérification** : Interrogez pour vérifier les données :
```bash
bq show data-pipeline-platform-484814:mdp_raw.google_ads_campaign_daily
```

## Avantages de l’architecture

- ✅ **Prêt pour la production** : Intégration BigQuery réelle, pas de mock
- ✅ **Extensible** : Ajoutez de nouvelles sources en étendant `DataSourceConnector`
- ✅ **Observable** : Tous les logs sont suivis dans BigQuery + Airflow UI
- ✅ **Scalable** : dbt transforme les données brutes pour l’analytique
- ✅ **Testé** : 55 tests dbt valident la qualité des données

## Prochaines étapes

1. **Configurer les vraies APIs** : Remplacez les fake APIs par les credentials réels Google Ads / Meta Ads
2. **Planifier l’ingestion** : Définir la planification du DAG dans `dags/google_ads_ingestion.py`
3. **Ajouter du monitoring** : Activez les contrôles de volume avec `src/monitoring/volume_checks.py`
4. **Construire des dashboards** : Connectez un outil BI (Looker, Data Studio) à `mdp_marts`

## Références

- [Client Python Google Cloud BigQuery](https://cloud.google.com/python/docs/reference/bigquery)
- [dbt BigQuery Adapter](https://docs.getdbt.com/docs/core/connect-data-platform/bigquery-setup)
- [Airflow Google Cloud Provider](https://airflow.apache.org/docs/apache-airflow-providers-google)