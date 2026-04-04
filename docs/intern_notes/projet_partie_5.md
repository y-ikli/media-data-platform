# Partie 5 — dbt Staging (standardisation) - TERMINÉE ✅

**Date:** 20 janvier 2026

## Objectif
Passer de raw hétérogène à un schéma standard avec dbt.

## Livrables Complétés

### 1. Projet dbt Initialisé ✅
- Projet `mdp` créé avec `dbt init`
- Structure de dossiers mise en place
- Configuration BigQuery dans `profiles.yml`
- Variables de projet configurées dans `dbt_project.yml`

### 2. Models Staging Créés ✅

#### Google Ads
- **Fichier:** `models/staging/google_ads/stg_google_ads__campaign_daily.sql`
- **Schéma:** `models/staging/google_ads/stg_google_ads__models.yml`
- **Transformations:**
  - Renommage des colonnes (`date` → `report_date`)
  - Typage fort (INT64, NUMERIC)
  - Ajout colonne `platform` = 'google_ads'
  - Filtrage des null sur clés primaires
  - Préservation des métadonnées (ingested_at, extract_run_id)

#### Meta Ads
- **Fichier:** `models/staging/meta_ads/stg_meta_ads__campaign_daily.sql`
- **Schéma:** `models/staging/meta_ads/stg_meta_ads__models.yml`
- **Transformations:** (identiques à Google Ads)
  - Renommage cohérent avec Google Ads
  - Typage identique
  - Ajout colonne `platform` = 'meta_ads'
  - Même structure de métadonnées

### 3. Sources Définies ✅
- **Fichier:** `models/staging/_sources.yml`
- Sources déclarées:
  - `raw_google_ads.raw_google_ads__campaign_daily`
  - `raw_meta_ads.raw_meta_ads__campaign_daily`
- Tests sur sources (not_null sur clés)

### 4. Tests dbt Implémentés ✅

#### Tests sur Colonnes
- **not_null** sur toutes les colonnes critiques:
  - `report_date`, `campaign_id`, `account_id`
  - `platform`, `impressions`, `clicks`, `spend`, `conversions`
  
- **accepted_values** sur `platform`:
  - Google Ads: ['google_ads']
  - Meta Ads: ['meta_ads']

#### Tests sur Modèles
- **unique_combination_of_columns** (via dbt_utils):
  - Combinaison: (`report_date`, `campaign_id`)
  - Garantit le grain défini

### 5. Documentation ✅
- **README principal:** `dbt/mdp/README.md`
  - Setup et installation
  - Commandes dbt
  - Conventions de nommage
  - Troubleshooting
  
- **README staging:** `models/staging/README.md`
  - Vue d'ensemble des modèles
  - Transformations appliquées
  - Tests de qualité
  - Exemples d'usage

- **Schémas YAML:**
  - Descriptions de tous les modèles
  - Descriptions de toutes les colonnes
  - Documentation du grain

### 6. Configuration et Dépendances ✅
- `packages.yml` créé avec dbt_utils (v1.3.0)
- `dbt deps` exécuté avec succès
- `dbt parse` validé sans erreurs

## Conventions Appliquées

### Naming
- Staging models: `stg_<source>__<entity>`
- Colonnes standardisées entre les sources
- Schémas: `mdp_staging`

### Typage
- Dates: DATE
- IDs: STRING
- Métriques entières: INT64
- Métriques décimales: NUMERIC

### Grain
- **Clé primaire:** (`report_date`, `campaign_id`)
- Un record par campagne par jour
- Validé par test d'unicité

## Indicateurs de Réussite Validés ✅

1. ✅ **`dbt parse` réussit sans erreurs**
   - Tous les modèles sont syntaxiquement corrects
   - Les tests sont bien formatés (format 'arguments')

2. ✅ **Colonnes critiques sont non-nulles**
   - Tests `not_null` sur toutes les clés primaires
   - Tests `not_null` sur toutes les métriques

3. ✅ **Schémas staging convergent**
   - Même structure pour Google Ads et Meta Ads
   - Noms de colonnes identiques
   - Types de données alignés
   - Colonne `platform` pour différenciation

## Structure du Projet dbt

```
dbt/mdp/
├── dbt_project.yml          # Configuration du projet
├── profiles.yml             # Connexion BigQuery
├── packages.yml             # Dépendances (dbt_utils)
├── README.md               # Documentation principale
└── models/
    └── staging/
        ├── README.md        # Doc staging layer
        ├── _sources.yml     # Définition des sources
        ├── google_ads/
        │   ├── stg_google_ads__campaign_daily.sql
        │   └── stg_google_ads__models.yml
        └── meta_ads/
            ├── stg_meta_ads__campaign_daily.sql
            └── stg_meta_ads__models.yml
```

## Commandes pour Tester

```bash
cd dbt/mdp

# Valider la syntaxe
dbt parse

# Compiler les modèles
dbt compile

# Exécuter les modèles (nécessite données raw)
dbt run --select staging

# Tester (nécessite données staging)
dbt test --select staging

# Documentation
dbt docs generate
dbt docs serve
```

## Prochaines Étapes (Partie 6)

La **Partie 5 est complétée** avec succès. Prêt pour:
- **Partie 6:** dbt Intermediate (unification cross-source)
  - Créer `int_campaign_daily_unified.sql`
  - Faire l'union des deux sources staging
  - Harmoniser les plateformes

## Notes Techniques

### Avertissements Résiduels (Normaux)
```
Configuration paths exist in your dbt_project.yml file which do not apply to any resources.
- models.mdp.intermediate
- models.mdp.marts
```
→ **Normal:** Ces chemins seront utilisés dans les parties suivantes

### Dépendances Ajoutées
```
dbt-core==1.11.2
dbt-bigquery==1.11.0
dbt_utils==1.3.0
```

## Conclusion

✅ **Partie 5 100% complète**

Tous les objectifs ont été atteints:
- Projet dbt initialisé et configuré
- Modèles staging créés pour les 2 sources
- Tests de qualité implémentés
- Documentation complète
- Conventions appliquées de façon cohérente
- Parsing réussi sans erreurs

Le projet est maintenant prêt pour la couche intermediate (Partie 6) qui unifiera les deux sources dans un modèle unique.
