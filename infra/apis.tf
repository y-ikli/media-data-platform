locals {
  apis = [
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sts.googleapis.com",
    "workflows.googleapis.com",
    "workflowexecutions.googleapis.com",
  ]
}

resource "google_project_service" "api" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}
