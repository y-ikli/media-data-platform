# Guide de Démarrage Rapide - Plateforme Data Marketing

**Système:** Linux (Ubuntu/Debian recommandé)

## Prérequis
- Docker & Docker Compose
- Python 3.11+
- Compte Google Cloud avec accès BigQuery
- Éditeur: nano (Ctrl+O pour enregistrer, Ctrl+X pour quitter)

## Installation

### 1. Cloner et Configurer
```bash
git clone <repo-url>
cd media-data-platform

# Installer les dépendances Python
pip install -r requirements.txt

# Installer les packages dbt
cd dbt/mdp
dbt deps
cd ../..
```

### 2. Configuration
```bash
# Copier le fichier de configuration exemple
cp config/settings.example.yaml config/settings.yaml

# Éditer avec vos détails GCP
nano config/settings.yaml
# (Ctrl+O pour enregistrer, Ctrl+X pour quitter)
```

### 3. Démarrer Airflow
```bash
# Démarrer les services Docker
docker compose up -d

# Attendre l'initialisation d'Airflow (~30 secondes)

# Accéder à l'interface Airflow
# URL: http://localhost:8080
# Utilisateur: admin
# Mot de passe: admin
```

## Utilisation

### Exécuter les Pipelines d'Ingestion
```bash
# Dans l'interface Airflow (http://localhost:8080):
# 1. Activer les DAGs
# 2. Déclencher manuellement:
#    - google_ads_ingestion_raw
#    - meta_ads_ingestion_raw
```

### Exécuter les Transformations dbt
```bash
# Option 1: Utiliser le script helper
./scripts/run_dbt.sh staging

# Option 2: Commandes dbt directes
cd dbt/mdp
dbt run --select staging
dbt test --select staging
```

### Voir la Documentation dbt
```bash
# Générer et servir la documentation
./scripts/run_dbt.sh docs

# Ou manuellement:
cd dbt/mdp
dbt docs generate
dbt docs serve --port 8080

# Ouvrir le navigateur: http://localhost:8080
```

## Statut du Projet

### Complété (Parties 0-7)
- [x] Environnement Docker avec Airflow
- [x] Structure datasets BigQuery
- [x] Ingestion Google Ads vers raw
- [x] Ingestion Meta Ads vers raw
- [x] Projet dbt initialisé
- [x] Modèles staging pour les deux sources
- [x] Couche intermediate (modèle unifié)
- [x] Couche marts (KPI métier)
- [x] Tests qualité données
- [x] Documentation complète

### Prochaines Étapes (Partie 8+)
- [ ] Orchestration Airflow end-to-end
- [ ] Monitoring qualité données
- [ ] Pipeline CI/CD
- [ ] Alertes et notifications

## Commandes Courantes

### Airflow
```bash
# Démarrer les services
docker compose up -d

# Arrêter les services
docker compose down

# Voir les logs
docker compose logs -f airflow-webserver

# Redémarrer les services
docker compose restart
```

### dbt
```bash
# Parser (valider la syntaxe)
dbt parse

# Compiler les modèles
dbt compile

# Exécuter tous les modèles
dbt run

# Exécuter une couche spécifique
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# Tester tout
dbt test

# Tester une couche spécifique
dbt test --select staging

# Générer la documentation
dbt docs generate
dbt docs serve
```

### Scripts Helper
```bash
# Opérations dbt
./scripts/run_dbt.sh parse
./scripts/run_dbt.sh staging
./scripts/run_dbt.sh docs
```

## Structure du Projet

```
media-data-platform/
├── dags/                          # DAGs Airflow
│   ├── google_ads_ingestion.py
│   ├── meta_ads_ingestion.py
│   └── hello_airflow.py
│
├── dbt/mdp/                       # Projet dbt
│   ├── models/
│   │   ├── staging/               # Couche standardisation
│   │   │   ├── google_ads/
│   │   │   │   ├── stg_google_ads__campaign_daily.sql
│   │   │   │   └── _models.yml
│   │   │   ├── meta_ads/
│   │   │   │   ├── stg_meta_ads__campaign_daily.sql
│   │   │   │   └── _models.yml
│   │   │   └── _sources.yml
│   │   ├── intermediate/          # Couche unification
│   │   │   ├── int_campaign_daily_unified.sql
│   │   │   └── _models.yml
│   │   └── marts/                 # Couche analytique
│   │       ├── mart_campaign_daily.sql
│   │       └── _models.yml
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── packages.yml
│
├── src/ingestion/                 # Modules d'ingestion
│   ├── google_ads/
│   └── meta_ads/
│
├── config/
│   └── settings.example.yaml
│
├── docs/
│   ├── architecture.md
│   ├── data_model.md
│   ├── kpi_reference.md
│   └── intern_notes/
│       ├── projet_partie_5.md
│       ├── projet_partie_6_7.md
│       └── project_steps.md
│
├── docker-compose.yaml
├── Dockerfile
├── requirements.txt
├── CHANGELOG.md
└── README.md
```

## Dépannage

### Interface Airflow inaccessible
```bash
# Vérifier le statut des services
docker compose ps

# Redémarrer les services
docker compose restart

# Consulter les logs
docker compose logs -f airflow-webserver
```

### Problèmes de connexion dbt
```bash
# Vérifier profiles.yml
nano dbt/mdp/profiles.yml
# (Ctrl+O pour enregistrer, Ctrl+X pour quitter)

# Tester la connexion
cd dbt/mdp
dbt debug
```

### Erreurs d'import dans les DAGs
```bash
# Vérifier PYTHONPATH dans les fichiers DAG
# S'assurer que src/ est ajouté à sys.path

# Redémarrer le scheduler Airflow
docker compose restart airflow-scheduler
```

### Éditer un fichier de configuration
```bash
# Utiliser nano (recommandé pour Linux)
nano <fichier>
# Ctrl+O pour enregistrer
# Ctrl+X pour quitter

# Ou utiliser vim si vous préférez
vim <fichier>
# :wq pour enregistrer et quitter
# :q! pour quitter sans enregistrer
```

## Ressources

- **Documentation:** `docs/`
- **Architecture:** `docs/architecture.md`
- **Modèle de données:** `docs/data_model.md`
- **Référence KPI:** `docs/kpi_reference.md`
- **Étapes du projet:** `docs/intern_notes/project_steps.md`
- **Détails Partie 5:** `docs/intern_notes/projet_partie_5.md`
- **Détails Parties 6-7:** `docs/intern_notes/projet_partie_6_7.md`

## Support

En cas de problème:
1. Consulter la documentation dans `docs/`
2. Vérifier les logs (Airflow ou dbt)
3. Se référer à la section dépannage ci-dessus
4. Consulter le CHANGELOG.md pour l'historique des modifications
