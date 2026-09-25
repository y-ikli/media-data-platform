# Référence des KPI

Calculés **une seule fois**, dans `mart_campaign_daily` (macro `safe_ratio`). Convention : un ratio vaut **NULL** (jamais 0, jamais une erreur) quand son dénominateur est nul ou absent.

| KPI | Formule | NULL si |
|---|---|---|
| CTR | clics / impressions | impressions = 0 |
| CPC | dépense / clics | clics = 0 |
| CPA | dépense / conversions | conversions = 0 ou non suivies |
| Taux de conversion | conversions / clics | clics = 0 |
| ROAS | valeur des conversions / dépense | dépense = 0 ou valeur non suivie |

Arrondis : CTR, taux de conversion, ROAS à 4 décimales ; CPC, CPA à 2.

## ROAS : changement de définition (v2)

Avant la v2, la colonne `roas` contenait `conversions / dépense`, un nombre de conversions par dollar, **pas** un ROAS : un retour sur dépense publicitaire se calcule avec un *revenu*. La colonne `conversion_value` (valeur des achats, USD) a été ajoutée à la zone raw ; `roas = conversion_value / spend`. Un tableau de bord qui lisait l'ancienne colonne doit être revu.

## Agrégation : sommer, ne pas moyenner

`mart_platform_monthly` calcule ses ratios depuis les sommes (Σ dépense / Σ clics). La moyenne des CPC journaliers donnerait autant de poids à un jour de 10 clics qu'à un jour de 10 000. Un test unitaire dbt le verrouille (`monthly_ratios_are_computed_from_sums_not_averaged`).

## Limites d'interprétation

- **Devise** : tout est en USD dans le pipeline ; aucune conversion n'est appliquée.
- **Conversions** : chaque plateforme a sa fenêtre d'attribution (clic, vue) et sa définition ; CPA et ROAS ne sont pas strictement comparables entre plateformes.
- **Meta** : les conversions viennent des actions d'achat configurées (`META_CONVERSION_ACTIONS`) ; sans pixel d'achat, elles sont NULL.
- **Fuseau horaire** : les jours sont ceux du compte publicitaire.
- **Données simulées** : filtrer sur `data_mode = 'real'` pour toute analyse qui ne doit contenir que des chiffres réels.
