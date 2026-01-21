# Documentation du script setup_bigquery.sh

Ce script permet de configurer les datasets et la connexion à BigQuery pour le projet.

## Utilisation

```bash
bash scripts/setup_bigquery.sh
```

## Rôle
- Crée les datasets nécessaires (raw, staging, intermediate, marts)
- Vérifie la connexion à BigQuery
- Affiche les messages de succès ou d'erreur

## Prérequis
- Variable d'environnement GOOGLE_APPLICATION_CREDENTIALS définie
- Accès au projet GCP

## Résultat attendu
- Tous les datasets sont créés et accessibles dans BigQuery
- Message de confirmation dans le terminal
