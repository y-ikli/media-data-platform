# Documentation du script verify_bigquery.sh

Ce script permet de vérifier la configuration et l'accès à BigQuery pour le projet.

## Utilisation

```bash
bash scripts/verify_bigquery.sh
```

## Rôle
- Vérifie la connexion à BigQuery
- Vérifie l'existence des datasets et tables
- Affiche les messages de diagnostic

## Prérequis
- Variable d'environnement GOOGLE_APPLICATION_CREDENTIALS définie
- Accès au projet GCP

## Résultat attendu
- Confirmation que BigQuery est prêt à être utilisé
- Affichage des éventuelles erreurs de configuration
