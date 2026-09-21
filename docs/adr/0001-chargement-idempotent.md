# ADR-0001 — Chargement idempotent par remplacement de fenêtre

**Statut** : acceptée

## Contexte
La v1 chargeait la zone raw en `WRITE_APPEND` (alors que la documentation annonçait `WRITE_TRUNCATE`) avec autodétection du schéma. Rejouer une ingestion dupliquait les lignes, ce qu'un script de déduplication rattrapait après coup.

## Options
1. `WRITE_TRUNCATE` sur la table : détruit tout l'historique à chaque run.
2. Une charge par partition (`table$AAAAMMJJ`) : idempotent, mais un job par jour ; 3 ans = ~1 100 jobs, proche du quota de 1 500 jobs de chargement par table et par jour.
3. Charge dans une table temporaire puis **transaction `DELETE` (fenêtre) + `INSERT`**.
4. `MERGE` sur `(date, campaign_id)` : idempotent, mais ne supprime pas une campagne disparue de la source.

## Décision
Option 3 : un job de chargement par fenêtre de 92 jours au plus, puis une transaction. Rejouer une fenêtre redonne le même état ; une campagne disparue de la source disparaît de la fenêtre. Le `DELETE` filtre la colonne de partition, donc seules les partitions de la fenêtre sont lues.

## Conséquences
- Une extraction **vide** ne supprime rien (protection contre une panne d'API qui vide silencieusement l'historique) : elle est journalisée en avertissement.
- Le schéma est explicite ; un lot invalide est rejeté avant chargement.
- La sémantique du remplacement est testée en exécutant les mêmes `DELETE`/`INSERT` sur DuckDB (`tests/unit/test_loader.py`) ; le chargement BigQuery lui-même est testé avec un client simulé, pas contre un vrai projet.
