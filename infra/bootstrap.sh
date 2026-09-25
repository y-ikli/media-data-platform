#!/usr/bin/env bash
# À exécuter UNE fois par environnement, avec un compte humain propriétaire du projet.
# Crée le bucket qui héberge l'état Terraform (versionné, accès uniforme). Le reste est géré par Terraform.
set -euo pipefail

PROJECT_ID="${1:?usage: bootstrap.sh <project_id> [region]}"
REGION="${2:-europe-west1}"
BUCKET="${PROJECT_ID}-tfstate"

gcloud services enable storage.googleapis.com --project "$PROJECT_ID"

if ! gcloud storage buckets describe "gs://${BUCKET}" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET}" --project "$PROJECT_ID" --location "$REGION" \
    --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage buckets update "gs://${BUCKET}" --versioning

echo "Bucket d'état prêt : gs://${BUCKET}"
echo "Suite : cd infra && terraform init -backend-config=\"bucket=${BUCKET}\" && terraform plan -var-file=envs/<env>.tfvars"
