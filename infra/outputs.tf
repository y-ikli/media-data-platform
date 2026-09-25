output "image_repository" {
  description = "Dépôt Artifact Registry où pousser l'image."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "deployer_service_account" {
  description = "À copier dans la variable GitHub GCP_DEPLOYER_SA."
  value       = google_service_account.deployer.email
}

output "workload_identity_provider" {
  description = "À copier dans la variable GitHub GCP_WIF_PROVIDER."
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "workflow" {
  value = google_workflows_workflow.daily.name
}

output "jobs" {
  value = [
    google_cloud_run_v2_job.ingest_meta.name,
    google_cloud_run_v2_job.ingest_google.name,
    google_cloud_run_v2_job.dbt.name,
  ]
}
