# ADR-0005 — GitHub → GCP par Workload Identity Federation, sans clé JSON

**Statut** : acceptée (code validé, non appliqué sur un projet réel)

## Contexte
La v1 authentifiait tout par un fichier de clé de compte de service. Une clé JSON est un secret durable, copiable, difficile à faire tourner ; l'héberger dans GitHub Secrets déplace le problème.

## Décision
- **CI → GCP** : Workload Identity Federation. GitHub émet un jeton OIDC éphémère par exécution ; GCP l'échange contre les droits du compte `mdp-deployer`. La condition du fournisseur n'accepte que **ce dépôt et cette branche**.
- **Jobs → BigQuery/Secret Manager** : comptes de service attachés aux jobs Cloud Run (Application Default Credentials) ; aucune clé n'existe.
- **Poste de développeur** : `gcloud auth application-default login`.
- Terraform ne crée que des *conteneurs* de secrets : les valeurs (jeton Meta) sont ajoutées hors bande pour ne jamais atterrir dans l'état Terraform.

## Conséquences
- Rien à faire tourner ni à révoquer ; une fuite de dépôt ne donne aucun accès.
- Le compte de déploiement n'a aucun accès aux données ni aux secrets : il ne peut que pousser une image et mettre à jour les jobs.
- `terraform apply` reste une action humaine (compte propriétaire) : la CI ne fait que valider l'infrastructure. Automatiser l'apply exigerait un compte aux droits étendus, à réserver à un environnement protégé.
