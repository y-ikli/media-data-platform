# ADR-0004 — Orchestration : Cloud Run Jobs + Workflows + Scheduler

**Statut** : acceptée (code validé, non appliqué sur un projet réel)

## Contexte
Le projet a d'abord embarqué Airflow, retiré en avril parce que surdimensionné pour un chargement ponctuel. Avec un chargement quotidien, il faut une orchestration : planifier, enchaîner (ingestion puis dbt), réessayer, alerter.

## Options
| Option | Pour | Contre |
|---|---|---|
| Cloud Composer (Airflow managé) | standard du marché, riche | > 300 €/mois d'environnement minimal : disproportionné pour ~10 000 lignes par jour |
| Airflow auto-hébergé | gratuit | machine à exploiter, mises à jour, sécurité |
| Scheduler + un seul script | simplissime | pas d'enchaînement, pas de parallélisme, échec partiel opaque |
| **Cloud Run Jobs + Workflows + Scheduler** | facturation à la seconde, sans serveur, enchaînement et parallélisme déclaratifs, compte de service par job | moins connu qu'Airflow, pas de DAG Python |

## Décision
Trois jobs (ingestion Meta, ingestion Google, dbt) d'une même image ; un workflow lance les deux ingestions en parallèle puis dbt, et **échoue si une étape échoue** : dbt ne construit jamais les marts sur des données incomplètes. Cloud Scheduler le déclenche chaque jour. Chaque job tourne sous son propre compte de service (moindre privilège).

## Conséquences
- Coût de l'ordre de quelques euros par mois.
- Le workflow est de la configuration versionnée (`infra/templates/daily.yaml.tftpl`), pas du code applicatif : la logique métier reste dans `mdp` et dbt, testée.
- Le passage à Airflow/Composer resterait simple : les jobs sont des commandes autonomes (`mdp-ingest …`, `dbt build`) que n'importe quel orchestrateur sait lancer.
- Fenêtre glissante de 3 jours à chaque exécution (`--lookback-days`) : une exécution manquée est rattrapée par la suivante sans intervention, grâce à l'idempotence ([ADR-0001](0001-chargement-idempotent.md)).
