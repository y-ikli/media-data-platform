#!/usr/bin/env bash
# Déploiement manuel de l'image du pipeline (le premier, ou sans passer par la CI).
#   scripts/deploy.sh [tag]        tag par défaut : le commit courant
# Prérequis : `terraform apply` fait dans infra/, gcloud connecté, Docker lancé.
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_REGION:-europe-west1}"
TAG="${1:-$(git rev-parse --short HEAD)}"
REGISTRY="${REGION}-docker.pkg.dev"
IMAGE="${REGISTRY}/${PROJECT_ID}/pipeline/adsdata:${TAG}"
JOBS=(ingest-google-ads ingest-meta-ads dbt-build)

echo "Image : ${IMAGE}"
gcloud auth configure-docker "${REGISTRY}" --quiet
docker build -t "${IMAGE}" .
docker push "${IMAGE}"

for job in "${JOBS[@]}"; do
  gcloud run jobs update "${job}" --image "${IMAGE}" --region "${REGION}" --project "${PROJECT_ID}" --quiet
done
echo "Jobs à jour : ${JOBS[*]}"
