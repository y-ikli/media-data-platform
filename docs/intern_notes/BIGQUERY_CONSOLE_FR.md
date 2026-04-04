# Guide BigQuery - Console Google Cloud

## Accéder à BigQuery Console

1. Ouvrir: https://console.cloud.google.com/bigquery
2. **Sélectionner le projet** (dropdown en haut)
   → `data-pipeline-platform-484814`

---

## Navigation - Interface Française

### Panneau Gauche (Explorateur)
```
┌─ data-pipeline-platform-484814 (Votre projet)
│
├─ 📁 mdp_raw (Ensemble de données)
│   ├─ google_ads_campaign_daily (Table)
│   └─ meta_ads_campaign_daily (Table)
│
├─ 📁 mdp_staging (Ensemble de données)
│   ├─ stg_google_ads__campaign_daily
│   └─ stg_meta_ads__campaign_daily
│
├─ 📁 mdp_intermediate (Ensemble de données)
│   └─ int_campaign_daily_unified
│
└─ 📁 mdp_marts (Ensemble de données) ← **Analytics!**
    └─ mart_campaign_daily
```

---

## Vérifier les Données - Étapes

### 1️⃣ Voir les Tables Brutes

1. Panneau gauche → `mdp_raw`
2. Clic sur `google_ads_campaign_daily`
3. Fenêtre de droite affiche:
   - **Aperçu** (Preview) - Voir les données
   - **Schéma** (Schema) - Voir les colonnes
   - **Détails** (Details) - Taille, nombre de lignes

### 2️⃣ Aperçu des Données

1. Clic sur table → Onglet **"Aperçu"**
2. Voir les 100 premières lignes
3. Colonnes visibles:
   - `date`, `campaign_id`, `campaign_name`
   - `impressions`, `clicks`, `conversions`, `cost_usd`
   - `ingested_at` (quand les données ont été chargées)
   - `source` ("google_ads" ou "meta_ads")

### 3️⃣ Schéma (Structure)

1. Clic sur table → Onglet **"Schéma"**
2. Voir toutes les colonnes et leurs types:
   - STRING, INTEGER, FLOAT, TIMESTAMP, etc.

### 4️⃣ Détails (Info)

1. Clic sur table → Onglet **"Détails"**
2. Voir:
   - **Nombre de lignes** (Nombre total d'enregistrements)
   - **Taille des données** (en Mo)
   - **Date de création**
   - **Dernière modification**

---

## Exécuter une Requête - Éditeur

### Menu Supérieur

```
┌─────────────────────────────────────────┐
│ + Nouvelle requête    Barre d'outil      │
└─────────────────────────────────────────┘
```

### Créer une Requête SQL

1. Clic sur **"+ Nouvelle requête"** (+ New Query)
2. Éditeur s'ouvre au centre
3. Copier/coller votre SQL:

```sql
-- Exemple: Compter les lignes
SELECT 
  COUNT(*) as total_lignes,
  source,
  MIN(ingested_at) as premiere_ingest,
  MAX(ingested_at) as derniere_ingest
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
GROUP BY source
```

### Exécuter la Requête

1. Clic sur bouton bleu **"Exécuter"** (Run)
2. Attendre 1-2 secondes
3. Résultats s'affichent en bas

---

## Éléments de l'Interface Français

| Français | English | Fonction |
|----------|---------|----------|
| **Aperçu** | Preview | Voir les données |
| **Schéma** | Schema | Structure de la table |
| **Détails** | Details | Infos (taille, lignes) |
| **Requête** | Query | SQL editor |
| **Exécuter** | Run | Lancer la requête |
| **Ensemble de données** | Dataset | Dossier de tables |
| **Table** | Table | Données |
| **Colonne** | Column | Champ |
| **Ligne** | Row | Enregistrement |
| **Type** | Type | Type de donnée |
| **Créer** | Create | Nouveau |
| **Importer** | Import | Charger des données |
| **Partage** | Share | Permissions |

---

## Workflow Complet en Français

### 1. Après Trigger DAG (Ingestion)

```
1. Panneau gauche → mdp_raw
2. Voir tables: google_ads_campaign_daily, meta_ads_campaign_daily
3. Clic sur google_ads_campaign_daily
4. Onglet "Aperçu" → Voir les données ingérées
5. Onglet "Détails" → Vérifier nombre de lignes > 0
```

### 2. Après dbt run (Transformations)

```
1. Panneau gauche → mdp_staging
2. Voir: stg_google_ads__campaign_daily, stg_meta_ads__campaign_daily
3. Panneau gauche → mdp_marts
4. Voir: mart_campaign_daily (données agrégées)
```

### 3. Écrire une Requête

```
1. Clic "+ Nouvelle requête"
2. Écrire SQL dans l'éditeur
3. Clic "Exécuter"
4. Voir résultats en bas
```

---

## Requêtes Utiles

### Compter les lignes

```sql
SELECT COUNT(*) as total
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
```

### Voir un échantillon

```sql
SELECT * 
FROM `data-pipeline-platform-484814.mdp_raw.google_ads_campaign_daily`
LIMIT 10
```

### Résumé par source

```sql
SELECT 
  source,
  COUNT(*) as nombre_enregistrements,
  SUM(impressions) as total_impressions,
  SUM(clicks) as total_clics,
  SUM(conversions) as total_conversions,
  SUM(cost_usd) as budget_total
FROM `data-pipeline-platform-484314.mdp_raw.google_ads_campaign_daily`
GROUP BY source
```

### Voir les marts

```sql
SELECT 
  date,
  source,
  SUM(impressions) as impressions,
  SUM(clicks) as clics,
  SUM(conversions) as conversions,
  ROUND(SUM(cost_usd), 2) as budget
FROM `data-pipeline-platform-484814.mdp_marts.mart_campaign_daily`
GROUP BY date, source
ORDER BY date DESC
LIMIT 30
```

---

## Navigation Rapide

| Action | Chemin |
|--------|--------|
| Voir données brutes | Gauche → `mdp_raw` → table → Onglet "Aperçu" |
| Voir structure | Gauche → `mdp_raw` → table → Onglet "Schéma" |
| Voir métadonnées | Gauche → `mdp_raw` → table → Onglet "Détails" |
| Écrire requête | **+ Nouvelle requête** → Éditeur → **Exécuter** |
| Voir résultats | Bas de l'écran → Onglet "Résultats" |
| Télécharger résultats | Résultats → Icône **Télécharger** (↓) |

---

## Boutons Importants (Haut de Page)

```
┌────────────────────────────────────────────────┐
│  + Nouvelle requête  |  Actualiser  |  ...     │
│  [Requête]           [SQL]         [Plus]      │
└────────────────────────────────────────────────┘
```

- **+ Nouvelle requête**: Créer une nouvelle requête SQL
- **Actualiser**: Recharger les données
- **...** (Menu): Options supplémentaires

---

## Raccourcis Clavier

| Touche | Action |
|--------|--------|
| `Ctrl + Entrée` | Exécuter la requête |
| `Ctrl + /` | Commenter/Décommenter |
| `Tab` | Indentation |

---

## 💡 Astuce

Si vous avez besoin d'aide:
1. Chercher le bouton **"?"** (Aide) en haut à droite
2. Documentation en français disponible
3. Chat support Google Cloud

---

## Prochaine Étape

Après vérifier que les données sont dans BigQuery:
```bash
cd dbt/mdp
dbt run
dbt test
```

Puis revisiter `mdp_marts.mart_campaign_daily` pour voir les données transformées et agrégées!
