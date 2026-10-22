# Tableau de bord Looker Studio

Le tableau de bord lit les tables du dataset `ads_marts`, construites par dbt. Aucun calcul métier n'est fait dans Looker Studio sauf les ratios agrégés (voir plus bas) : les définitions sont dans dbt, à un seul endroit.

## Créer le rapport

Ce lien crée un rapport déjà branché sur `mart_campaign_daily`, avec la date de partition comme période :

```
https://lookerstudio.google.com/reporting/create?c.mode=edit&r.reportName=Media%20Analytics%20Platform&ds.connector=bigQuery&ds.type=TABLE&ds.projectId=ads-media-platform&ds.datasetId=ads_marts&ds.tableId=mart_campaign_daily&ds.isPartitioned=true&ds.datasourceName=mart_campaign_daily
```

Ajouter ensuite deux sources (**Ajouter des données → BigQuery → ads-media-platform → ads_marts**) : `mart_platform_monthly` et `dim_campaign`.

## Champs calculés : ne jamais faire la moyenne d'un ratio

Une moyenne de CTR journaliers donne autant de poids à un jour de 100 impressions qu'à un jour de 100 000. Les ratios affichés pour une période se recalculent depuis les sommes. Dans la source `mart_campaign_daily`, ajouter ces champs :

| Champ | Formule |
|---|---|
| CTR période | `SUM(clicks) / SUM(impressions)` |
| CPC période | `SUM(spend) / SUM(clicks)` |
| CPA période | `SUM(spend) / SUM(conversions)` |
| Taux de conversion période | `SUM(conversions) / SUM(clicks)` |
| ROAS période | `SUM(conversion_value) / SUM(spend)` |

Les colonnes `ctr`, `cpc`, `cpa`, `conversion_rate` et `roas` de la table restent justes au grain campagne × jour (tableaux détaillés).

## Pages

**1. Vue d'ensemble**
- Contrôles : période (`date`), plateforme (`platform`), origine des données (`data_mode`).
- Fiches de score : dépense, valeur des conversions, ROAS période, CPA période.
- Série temporelle : dépense et valeur des conversions par jour.

**2. Meta contre Google** (source `mart_platform_monthly`)
- Barres groupées : ROAS par mois et par plateforme.
- Tableau : mois, plateforme, dépense, conversions, CPA, ROAS.

**3. Campagnes**
- Tableau triable : campagne (nom via `dim_campaign`), plateforme, dépense, conversions, CPA période, ROAS période, avec mise en forme conditionnelle sur le ROAS.

## Honnêteté des données

Google Ads est simulé. Ajouter sur chaque page un filtre ou une mention visible sur `data_mode` (par exemple une fiche « Part de données simulées »). Une table qui mélange réel et simulé sans le dire n'est pas présentable.

## Partage

- Identifiants de la source : **identifiants du propriétaire**, pour que les lecteurs n'aient besoin d'aucun accès à Google Cloud.
- Chaque ouverture du rapport lance des requêtes BigQuery : les tables `ads_marts` sont petites, et le cache de Looker Studio (12 heures par défaut) limite les relectures.
