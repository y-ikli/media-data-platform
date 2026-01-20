# Projet dbt - Plateforme Data Marketing

## Aperçu
Ce projet dbt transforme les données publicitaires brutes (Google Ads, Meta Ads) en tables analytiques standardisées pour la BI.

**Pour l'architecture et le modèle de données complet:** voir [docs/data_model.md](../../docs/data_model.md)

## Structure du Projet
```
models/
├── staging/           # Données sources standardisées
│   ├── google_ads/    # Modèles staging Google Ads
│   ├── meta_ads/      # Modèles staging Meta Ads
│   └── _sources.yml   # Définitions des sources
├── intermediate/      # Modèles unifiés cross-platform
└── marts/             # Data products prêts pour la BI
```

## Installation

### Prérequis
- dbt-core >= 1.7.0
- dbt-bigquery >= 1.7.0
- Accès au projet BigQuery

### Configuration
1. Installer les dépendances dbt:
```bash
dbt deps
```

2. Vérifier [profiles.yml](profiles.yml) avec vos détails BigQuery:
```yaml
mdp:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: VOTRE_PROJET_ID
      dataset: mdp_staging
      location: europe-west1
```

3. Vérifier les variables dans [dbt_project.yml](dbt_project.yml):
```yaml
vars:
  gcp_project: VOTRE_PROJET_ID
  raw_dataset: mdp_raw
  staging_dataset: mdp_staging
  marts_dataset: mdp_marts
```

## Utilisation

### Exécuter les Modèles
```bash
# Tous les modèles
dbt run

# Une couche spécifique
dbt run --select staging
dbt run --select intermediate
dbt run --select marts

# Un modèle spécifique
dbt run --select stg_google_ads__campaign_daily

# Avec full refresh
dbt run --full-refresh
```

### Tester la Qualité des Données
```bash
# Tous les tests
dbt test

# Tests d'une couche
dbt test --select staging

### Générer la Documentation
```bash
# Générer et servir la documentation
dbt docs generate
dbt docs serve
```

## Couches dbt

### Staging
Standardise les données brutes avec:
- Nommage cohérent des colonnes
- Typage correct
- Gestion des nulls
- Ajout du tag plateforme
- Préservation des métadonnées

**Modèles:**
- `stg_google_ads__campaign_daily`: Métriques quotidiennes Google Ads
- `stg_meta_ads__campaign_daily`: Métriques quotidiennes Meta Ads

### Intermediate
Unifie les données cross-platform:
- `int_campaign_daily_unified`: UNION des deux plateformes

### Marts
Data products avec KPI calculés:
- `mart_campaign_daily`: Table BI avec CTR, CPA, ROAS, CPC, Conversion Rate

**Grain:** `report_date` + `campaign_id` + `platform`

## Tests Qualité
- **not_null**: Clés primaires et métriques critiques
- **accepted_values**: Validation des plateformes
- **unique_combination**: Respect du grain
- **accepted_range**: Métriques ≥ 0
- **recency**: Données récentes (≤7 jours)

## Conventions

### Nommage
- Staging: `stg_<source>__<entity>`
- Intermediate: `int_<entity>_<transformation>`
- Marts: `mart_<domain>_<grain>`

### Matérialisation
- Staging: `view` (légères, toujours fraîches)
- Intermediate: `view` (transformations réutilisables)
- Marts: `table` (optimisées pour requêtes BI)

### Schémas BigQuery
- Raw: `mdp_raw`
- Staging: `mdp_staging`
- Intermediate: `mdp_intermediate`
- Marts: `mdp_marts`

## Workflow de Développement

1. Créer une branche pour nouvelle feature
2. Développer modèles dans la couche appropriée
3. Ajouter tests de qualité
4. Documenter dans fichiers _models.yml
5. Valider avec `dbt parse` et `dbt test`
6. Exécuter avec `dbt run`
7. Review et merge

## Dépannage

### Problèmes Courants

**Erreur: Unable to find profile**
- Vérifier emplacement de `profiles.yml` (~/.dbt/ ou racine projet)
- Vérifier que le nom du profile correspond à `dbt_project.yml`

**Erreur: Table not found**
- S'assurer que les tables raw existent dans BigQuery
- Vérifier les noms de datasets dans les variables
- Vérifier les permissions BigQuery

**Warning: Configuration paths exist which do not apply**
- Normal pour structure de projet incomplète
- Se résoudra quand toutes les couches seront créées

## Ressources
- [Documentation dbt](https://docs.getdbt.com/)
- [Best Practices dbt](https://docs.getdbt.com/guides/best-practices)
- [Référence SQL BigQuery](https://cloud.google.com/bigquery/docs/reference/standard-sql)
- [Communauté dbt Slack](https://community.getdbt.com/)
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices
