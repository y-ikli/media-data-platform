resource "google_workflows_workflow" "daily" {
  name            = "mdp-daily"
  region          = var.region
  description     = "Ingestion Meta + Google en parallèle, puis dbt build"
  service_account = google_service_account.workflow.email
  labels          = local.labels

  source_contents = templatefile("${path.module}/templates/daily.yaml.tftpl", {
    project_id = var.project_id
    region     = var.region
    meta_job   = google_cloud_run_v2_job.ingest_meta.name
    google_job = google_cloud_run_v2_job.ingest_google.name
    dbt_job    = google_cloud_run_v2_job.dbt.name
  })

  depends_on = [google_project_service.api]
}

resource "google_cloud_scheduler_job" "daily" {
  name        = "mdp-daily"
  region      = var.region
  description = "Déclenche le workflow mdp-daily"
  schedule    = var.schedule_cron
  time_zone   = var.schedule_timezone
  paused      = var.schedule_paused

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/${google_workflows_workflow.daily.id}/executions"
    body        = base64encode(jsonencode({ argument = "{}" }))
    headers     = { "Content-Type" = "application/json" }

    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  retry_config {
    retry_count = 1
  }

  depends_on = [google_project_service.api]
}
