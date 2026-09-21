# ADR-0002 — Tester dbt sur DuckDB, sans identifiants

**Statut** : acceptée

## Contexte
La CI de la v1 exécutait `dbt compile ... || echo`, ce qui ne pouvait jamais échouer, et aucun test de données ne tournait hors d'un projet BigQuery.

## Décision
Le projet dbt est écrit pour s'exécuter sur deux moteurs : BigQuery (prod) et DuckDB (tests, CI). Les différences sont isolées dans quelques macros (`date_offset`, `month_start`) et dans la configuration conditionnelle (`insert_overwrite` et partitionnement sur BigQuery seulement). La zone raw locale est produite par les vrais connecteurs simulés, enrichis et validés comme en production, avec un jeu de janvier volontairement chargé deux fois.

La CI exécute : les modèles, les 47 tests de données, les tests unitaires dbt (déduplication, KPI à dénominateur nul, agrégation mensuelle), le scénario incrémental (fenêtre glissante, `reprocess_from`, `--full-refresh`), sqlfluff, et un `dbt parse` sur la cible BigQuery.

## Limites assumées
Un modèle peut passer sur DuckDB et échouer sur BigQuery (dialecte). Les macros de dates évitent le piège connu `DATE` contre `DATETIME`. Le SQL rendu pour BigQuery n'est pas exécuté en CI ; c'est le prochain pas (projet de test dédié, authentification par Workload Identity Federation).
