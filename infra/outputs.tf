output "datasets" {
  description = "Datasets BigQuery créés, par couche."
  value       = { for layer, dataset in google_bigquery_dataset.layer : layer => dataset.dataset_id }
}

output "image_repository" {
  description = "Adresse où pousser l'image du pipeline."
  value       = local.image_repository
}

output "jobs" {
  description = "Jobs Cloud Run, par rôle."
  value       = local.job_names
}

output "workflow" {
  description = "Workflow quotidien."
  value       = google_workflows_workflow.daily.name
}

output "github_actions" {
  description = "Valeurs à déclarer comme variables du dépôt GitHub (Settings → Variables)."
  value = {
    GCP_PROJECT_ID                 = var.project_id
    GCP_REGION                     = var.region
    GCP_WORKLOAD_IDENTITY_PROVIDER = google_iam_workload_identity_pool_provider.github.name
    GCP_DEPLOYER_SERVICE_ACCOUNT   = google_service_account.pipeline["deployer"].email
  }
}
