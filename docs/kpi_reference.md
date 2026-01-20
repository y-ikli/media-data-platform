# Guide de Référence des KPI - Plateforme Data Marketing

## Aperçu

Ce document définit les KPI calculés dans la table `mart_campaign_daily`. Tous les KPI utilisent `safe_divide()` pour éviter les valeurs inf/NaN.

## Métriques de Base (données brutes)

| Métrique | Type | Source | Description |
|----------|------|--------|-------------|
| impressions | INT64 | API | Nombre de fois où les annonces ont été affichées |
| clicks | INT64 | API | Nombre de clics sur les annonces |
| spend | NUMERIC | API | Dépense publicitaire totale (devise native) |
| conversions | INT64 | API | Nombre de conversions suivies |

## KPI Calculés

### 1. CTR (Taux de Clic)

**Formule:**
```sql
CTR = clicks / impressions
```

**Type:** NUMERIC (échelle 0-1, ex: 0.025 = 2.5%)

**Calcul:**
```sql
case 
  when impressions > 0 then round(safe_divide(clicks, impressions), 4)
  else null 
end as ctr
```

**Interprétation:**
- Mesure l'attrait et la pertinence de l'annonce
- CTR élevé = annonces plus engageantes
- Plage typique: 0.5% - 3% selon le secteur
- Inférieur aux attentes: ciblage ou créatif problématique

**Cas d'usage:**
- Tests A/B de créatifs
- Identification des campagnes performantes
- Comparaisons avec concurrents

**Null quand:** impressions = 0

---

### 2. CPA (Coût par Acquisition)

**Formule:**
```sql
CPA = spend / conversions
```

**Type:** NUMERIC (montant en devise)

**Calcul:**
```sql
case 
  when conversions > 0 then round(safe_divide(spend, conversions), 2)
  else null 
end as cpa
```

**Interprétation:**
- Mesure le coût pour acquérir un client/conversion
- CPA bas = campagnes plus efficaces
- Très dépendant du modèle métier et du type de conversion
- Plage typique: Varie par secteur (ex: SaaS: $50-500, E-commerce: $5-50)

**Cas d'usage:**
- Optimisation de l'allocation budgétaire
- Comparaison de performance entre campagnes
- Analyse ROI par campagne

**Null quand:** conversions = 0

---

### 3. ROAS (Retour sur Investissement Publicitaire)

**Formule:**
```sql
ROAS = conversions / spend
```

**Type:** NUMERIC (ratio)

**Calcul:**
```sql
case 
  when spend > 0 then round(safe_divide(conversions, spend), 4)
  else null 
end as roas
```

**Interprétation:**
- Mesure le retour pour chaque unité de devise dépensée
- ROAS > 1.0 = Rentable (gain supérieur à dépense)
- ROAS = 1.0 = Équilibre
- ROAS < 1.0 = Perte (dépense supérieure au gain)
- Objectif typique: ROAS > 2.0 (2x retour)

**Cas d'usage:**
- Évaluation de la rentabilité globale
- Décisions de scaling budgétaire
- Validation de stratégie

**Null quand:** spend = 0

**Note:** ROAS varie beaucoup selon le secteur. E-commerce: 2-4x, lead gen: 1.5-2x.

---

### 4. CPC (Coût par Clic)

**Formule:**
```sql
CPC = spend / clicks
```

**Type:** NUMERIC (montant en devise)

**Calcul:**
```sql
case 
  when clicks > 0 then round(safe_divide(spend, clicks), 2)
  else null 
end as cpc
```

**Interprétation:**
- Coût moyen pour générer un clic
- CPC bas = génération de clics plus efficace
- Influencé par la plateforme et la stratégie d'enchères
- Plage typique: Variable (ex: Google: $0.50-3.00)

**Cas d'usage:**
- Optimisation de la stratégie d'enchères
- Comparaison entre plateformes
- Comparaison d'efficacité des coûts

**Null quand:** clicks = 0

---

### 5. Taux de Conversion

**Formule:**
```sql
Taux de Conversion = conversions / clicks
```

**Type:** NUMERIC (échelle 0-1, ex: 0.05 = 5%)

**Calcul:**
```sql
case 
  when clicks > 0 then round(safe_divide(conversions, clicks), 4)
  else null 
end as conversion_rate
```

**Interprétation:**
- Pourcentage de clics qui résultent en conversions
- Taux de conversion élevé = meilleure page d'atterrissage ou offre
- Influencé par UX, ciblage et pertinence de l'offre
- Plage typique: 1% - 10% selon le secteur

**Cas d'usage:**
- Optimisation de la page d'atterrissage
- Évaluation du ciblage d'audience
- Analyse d'entonnoir

**Null quand:** clicks = 0

**Benchmarks courants:**
- Produit e-commerce: 1-3%
- Essai SaaS: 3-10%
- Génération de leads: 2-5%
- Newsletter: 5-15%

---

## Considérations de Sécurité

### Gestion de Division par Zéro

Tous les KPI utilisent la fonction `safe_divide()`:

```sql
safe_divide(numerateur, dénominateur)
```

**Comportement:**
- Retourne NULL si dénominateur = 0
- Ne retourne jamais inf, -inf, ou NaN
- Prévient les échecs ETL et données invalides

**Exemple:**
```sql
-- Sans safe_divide (mauvais)
SELECT clicks / impressions  -- Retourne inf si impressions=0

-- Avec safe_divide (bon)
SELECT safe_divide(clicks, impressions)  -- Retourne NULL si impressions=0
```

### Arrondi

Tous les KPI sont arrondis correctement:
- KPI en devise (CPA, CPC): 2 décimales
- KPI ratios (CTR, ROAS, Conversion Rate): 4 décimales

**Exemple:**
```sql
round(safe_divide(spend, clicks), 2) as cpc  -- 2.45, pas 2.4526
```

---

## Validation de la Qualité des Données

### Tests Appliqués aux KPI

Tous les KPI dans `mart_campaign_daily` sont validés avec:

1. **Test accepted_range**
   ```sql
   -- Toutes les métriques >= 0
   KPI >= 0
   ```
   Garantit pas de valeurs négatives

2. **Vérification not_null** sur les dénominateurs
   ```sql
   impressions > 0, clicks > 0, spend > 0, conversions > 0
   ```
   Garantit jamais de KPI invalides

3. **Unicité du grain**
   ```sql
   unique_combination_of_columns:
     - report_date
     - campaign_id
     - platform
   ```
   Garantit une ligne par campagne par jour par plateforme

---

## Requêtes d'Analyse Typiques

### Top Campagnes par ROAS

```sql
select
  campaign_name,
  platform,
  sum(spend) as total_spend,
  sum(conversions) as total_conversions,
  round(avg(roas), 4) as avg_roas
from mart_campaign_daily
where report_date >= current_date() - 30
group by campaign_name, platform
having sum(conversions) > 0
order by avg_roas desc
limit 10;
```

### Comparaison de Performance par Plateforme

```sql
select
  platform,
  count(distinct campaign_id) as nb_campagnes,
  sum(impressions) as total_impressions,
  avg(ctr) as ctr_moyen,
  sum(spend) as depense_totale,
  round(avg(cpa), 2) as cpa_moyen,
  round(avg(roas), 4) as roas_moyen
from mart_campaign_daily
where report_date >= current_date() - 7
group by platform;
```

### Analyse de Tendance Quotidienne

```sql
select
  report_date,
  campaign_name,
  impressions,
  clicks,
  ctr,
  spend,
  conversions,
  cpa,
  roas
from mart_campaign_daily
where campaign_name = 'Brand Search'
  and report_date >= current_date() - 30
order by report_date desc;
```

### Notation d'Efficacité

```sql
select
  campaign_name,
  platform,
  case 
    when roas >= 3 then 'Excellent'
    when roas >= 2 then 'Bon'
    when roas >= 1 then 'Acceptable'
    else 'À Améliorer'
  end as notation_efficacite,
  round(roas, 4) as roas,
  round(cpa, 2) as cpa
from mart_campaign_daily
where report_date = current_date() - 1
order by notation_efficacite, roas desc;
```

---

## Limitations et Considérations

### Devise

- `spend` est en devise native de la plateforme (peut différer entre les plateformes)
- Pour comparaisons cross-platform, conversion de devise nécessaire
- Les KPI impliquant spend (CPA, CPC, ROAS) sont spécifiques à la devise

### Définition de Conversion

- La définition de "conversion" varie selon le métier
- S'assurer du tracking cohérent entre plateformes
- Peut nécessiter tracking séparé pour types de conversion différents

### Différences Plateformes

- **Google Ads:** Généralement plus cher par clic, taux de conversion plus haut
- **Meta Ads:** CPC généralement plus bas, tracking de conversion différent
- Les comparaisons directes doivent tenir compte de ces différences

### Fuseau Horaire

- Toutes les dates basées sur fuseau natif
- Considérer les différences de fuseau en analyse quotidienne
- Peut vouloir normaliser à un fuseau standard pour reporting

