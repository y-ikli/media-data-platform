# Un compte de service par rôle, chacun avec le strict nécessaire.
locals {
  service_accounts = {
    ingestion    = "Ingestion des API publicitaires vers ads_raw"
    transform    = "Transformation dbt : ads_raw vers ads_staging et ads_marts"
    orchestrator = "Workflow quotidien et son déclencheur"
    deployer     = "Déploiement depuis GitHub Actions"
  }
}

resource "google_service_account" "pipeline" {
  for_each = local.service_accounts

  account_id   = "ads-${each.key}"
  display_name = each.value

  depends_on = [google_project_service.enabled]
}

# --- BigQuery -------------------------------------------------------------------------------
# Lancer des requêtes et des chargements est un droit du projet ; les données, un droit par dataset.
resource "google_project_iam_member" "bigquery_job_user" {
  for_each = toset(["ingestion", "transform"])

  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = google_service_account.pipeline[each.value].member
}

resource "google_bigquery_dataset_iam_member" "access" {
  for_each = {
    ingestion_writes_raw   = { dataset = "raw", account = "ingestion", role = "roles/bigquery.dataEditor" }
    transform_reads_raw    = { dataset = "raw", account = "transform", role = "roles/bigquery.dataViewer" }
    transform_owns_staging = { dataset = "staging", account = "transform", role = "roles/bigquery.dataEditor" }
    transform_owns_marts   = { dataset = "marts", account = "transform", role = "roles/bigquery.dataEditor" }
  }

  dataset_id = google_bigquery_dataset.layer[each.value.dataset].dataset_id
  role       = each.value.role
  member     = google_service_account.pipeline[each.value.account].member
}

# --- Orchestration --------------------------------------------------------------------------
resource "google_cloud_run_v2_job_iam_member" "orchestrator_runs_jobs" {
  for_each = local.job_names

  name     = each.value
  location = var.region
  role     = "roles/run.invoker"
  member   = google_service_account.pipeline["orchestrator"].member

  depends_on = [google_cloud_run_v2_job.ingest, google_cloud_run_v2_job.transform]
}

resource "google_project_iam_member" "orchestrator" {
  # run.viewer : suivre l'exécution des jobs ; workflows.invoker : être déclenché par Scheduler.
  for_each = toset(["roles/run.viewer", "roles/workflows.invoker", "roles/logging.logWriter"])

  project = var.project_id
  role    = each.value
  member  = google_service_account.pipeline["orchestrator"].member
}

# --- Déploiement ----------------------------------------------------------------------------
resource "google_artifact_registry_repository_iam_member" "deployer_pushes_images" {
  repository = google_artifact_registry_repository.images.name
  location   = var.region
  role       = "roles/artifactregistry.writer"
  member     = google_service_account.pipeline["deployer"].member
}

resource "google_project_iam_member" "deployer_updates_jobs" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = google_service_account.pipeline["deployer"].member
}

resource "google_service_account_iam_member" "deployer_acts_as_runtime" {
  # Mettre à jour un job qui tourne sous un compte de service exige de pouvoir agir en son nom.
  for_each = toset(["ingestion", "transform"])

  service_account_id = google_service_account.pipeline[each.value].name
  role               = "roles/iam.serviceAccountUser"
  member             = google_service_account.pipeline["deployer"].member
}
