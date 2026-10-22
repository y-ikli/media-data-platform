resource "google_workflows_workflow" "daily" {
  name            = "pipeline-quotidien"
  region          = var.region
  description     = "Ingestion Meta Ads et Google Ads, puis transformation dbt."
  service_account = google_service_account.pipeline["orchestrator"].id
  labels          = local.labels

  source_contents = templatefile("${path.module}/templates/daily.yaml.tftpl", {
    project       = var.project_id
    region        = var.region
    ingest_jobs   = { for source, _ in local.ingest_jobs : source => local.job_names[source] }
    transform_job = local.job_names["transform"]
  })

  deletion_protection = false

  depends_on = [google_project_service.enabled]
}

resource "google_cloud_scheduler_job" "daily" {
  name             = "pipeline-quotidien"
  region           = var.region
  description      = "Déclenche le workflow quotidien."
  schedule         = var.schedule
  time_zone        = var.time_zone
  attempt_deadline = "320s"

  http_target {
    http_method = "POST"
    uri         = "https://workflowexecutions.googleapis.com/v1/${google_workflows_workflow.daily.id}/executions"
    body        = base64encode("{}")

    oauth_token {
      service_account_email = google_service_account.pipeline["orchestrator"].email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [google_project_iam_member.orchestrator]
}
