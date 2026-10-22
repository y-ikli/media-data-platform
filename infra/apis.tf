# API Google Cloud utilisées par le projet.
locals {
  services = toset([
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sts.googleapis.com",
    "workflows.googleapis.com",
  ])
}

resource "google_project_service" "enabled" {
  for_each = local.services

  service = each.value

  # Si une API est retirée de la liste : l'oublier, sans la couper (ce qui casserait le projet).
  disable_on_destroy = false
  deletion_policy    = "ABANDON"
}

# L'API BigQuery était déclarée seule à l'étape précédente : on déplace sa ligne dans le state
# au lieu de la supprimer puis la recréer.
moved {
  from = google_project_service.bigquery
  to   = google_project_service.enabled["bigquery.googleapis.com"]
}
