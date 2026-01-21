#!/bin/bash
# Diagnostic script pour BigQuery vide

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                  DIAGNOSTIC BIGQUERY VIDE                             ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Étape 1: Vérifier credentials
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1  VÉRIFIER CREDENTIALS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ ERREUR: GOOGLE_APPLICATION_CREDENTIALS n'est PAS défini!"
    echo ""
    echo "SOLUTION:"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=~/path/to/gcp-key.json"
    echo ""
    echo "Exemple:"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=~/gcp-key.json"
    echo ""
    exit 1
else
    echo "✓ GOOGLE_APPLICATION_CREDENTIALS = $GOOGLE_APPLICATION_CREDENTIALS"
    
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "❌ ERREUR: Le fichier n'existe pas!"
        echo "  Chemin: $GOOGLE_APPLICATION_CREDENTIALS"
        exit 1
    else
        echo "✓ Fichier credentials trouvé"
    fi
fi

echo ""

# Étape 2: Vérifier connexion BigQuery
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2 VÉRIFIER CONNEXION BIGQUERY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
import sys
from google.cloud import bigquery

try:
    client = bigquery.Client()
    project_id = client.project
    print(f"✓ Connexion BigQuery OK")
    print(f"✓ Project ID: {project_id}")
except Exception as e:
    print(f"❌ Erreur connexion: {str(e)}")
    sys.exit(1)
PYEOF

echo ""

# Étape 3: Vérifier datasets
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3  VÉRIFIER DATASETS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
from google.cloud import bigquery

client = bigquery.Client()
datasets = list(client.list_datasets())

print(f"Datasets trouvés: {len(datasets)}")
print("")

required_datasets = ["mdp_raw", "mdp_staging", "mdp_intermediate", "mdp_marts"]
found_datasets = [ds.dataset_id for ds in datasets]

for ds in required_datasets:
    if ds in found_datasets:
        print(f"  ✓ {ds}")
    else:
        print(f"  ❌ {ds} MANQUANT")

print("")

if len([ds for ds in required_datasets if ds in found_datasets]) < 4:
    print("⚠️  SOLUTION: Créer les datasets")
    print("  bash scripts/setup_bigquery.sh")
PYEOF

echo ""

# Étape 4: Vérifier tables
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4  VÉRIFIER TABLES DANS MDП_RAW"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
from google.cloud import bigquery

client = bigquery.Client()
project_id = client.project

try:
    dataset = client.get_dataset(f"{project_id}.mdp_raw")
    tables = list(client.list_tables(dataset))
    
    if len(tables) == 0:
        print("❌ AUCUNE TABLE dans mdp_raw!")
        print("")
        print("CAUSE PROBABLE: Les DAGs n'ont pas été triggés")
        print("")
        print("SOLUTION:")
        print("  1. Ouvrir http://localhost:8080 (Airflow)")
        print("  2. Trigger DAG: google_ads_ingestion_raw")
        print("  3. Attendre que le DAG complète (~2 min)")
        print("  4. Vérifier à nouveau: bash scripts/diagnose_bigquery.sh")
        print("")
    else:
        print(f"✓ {len(tables)} table(s) trouvée(s) dans mdp_raw")
        for table in tables:
            print(f"  - {table.table_id}")
            
except Exception as e:
    print(f"❌ Erreur: {str(e)}")
    print("Le dataset mdp_raw n'existe pas")
    print("Solution: bash scripts/setup_bigquery.sh")

PYEOF

echo ""

# Étape 5: Vérifier données
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5  VÉRIFIER DONNÉES DANS LES TABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 << 'PYEOF'
from google.cloud import bigquery

client = bigquery.Client()
project_id = client.project

try:
    query = f"""
    SELECT TABLE_NAME, ROW_COUNT
    FROM `{project_id}.mdp_raw.__TABLES__`
    """
    results = client.query(query).result()
    
    rows_list = list(results)
    if len(rows_list) == 0:
        print("❌ Aucune table ou données!")
    else:
        for row in rows_list:
            table_name = row['TABLE_NAME']
            row_count = row['ROW_COUNT']
            if row_count == 0:
                print(f"⚠️  {table_name}: {row_count} lignes (VIDE)")
            else:
                print(f"✓ {table_name}: {row_count} lignes")
                
except Exception as e:
    print(f"❌ Erreur: {str(e)}")

PYEOF

echo ""

# Étape 6: Vérifier Airflow
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6  VÉRIFIER AIRFLOW RUNNING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if docker ps | grep -q airflow-webserver; then
    echo "✓ Airflow webserver est running"
else
    echo "❌ Airflow n'est PAS running"
    echo ""
    echo "SOLUTION: Démarrer Airflow"
    echo "  docker compose up -d"
fi

echo ""

# Étape 7: Checklist finale
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                        CHECKLIST DIAGNOSTIC                           ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Vous devez faire ceci dans l'ordre:"
echo ""
echo "1  SETUP (une seule fois)"
echo "    $ export GOOGLE_APPLICATION_CREDENTIALS=~/gcp-key.json"
echo "    $ bash scripts/setup_bigquery.sh"
echo "    ✓ Vérifier: 4 datasets créés"
echo ""
echo "2 DÉMARRER AIRFLOW"
echo "    $ docker compose up -d"
echo "    ✓ Vérifier: http://localhost:8080 accessible"
echo ""
echo "3  TRIGGER INGESTION DAG"
echo "    Dans Airflow UI:"
echo "    - DAGs → google_ads_ingestion_raw"
echo "    - Clic: Trigger DAG"
echo "    - Attendre: DAG complète (✓ status)"
echo ""
echo "4  VÉRIFIER DONNÉES"
echo "    $ bash scripts/verify_bigquery.sh"
echo "    $ bq ls data-pipeline-platform-484814:mdp_raw"
echo ""
echo "5  TRANSFORMATIONS (optionnel)"
echo "    $ cd dbt/mdp && dbt run"
echo ""

echo "═══════════════════════════════════════════════════════════════════════"
echo ""
