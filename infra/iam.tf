# Un compte de service par rôle, droits limités au strict nécessaire, accordés au niveau du jeu de données.
resource "google_service_account" "ingest" {
  account_id   = "mdp-ingest"
  display_name = "MDP — jobs d'ingestion"
  depends_on   = [google_project_service.api]
}

resource "google_service_account" "dbt" {
  account_id   = "mdp-dbt"
  display_name = "MDP — transformations dbt"
  depends_on   = [google_project_service.api]
}

resource "google_service_account" "workflow" {
  account_id   = "mdp-workflow"
  display_name = "MDP — orchestration (Workflows)"
  depends_on   = [google_project_service.api]
}

resource "google_service_account" "scheduler" {
  account_id   = "mdp-scheduler"
  display_name = "MDP — déclenchement planifié"
  depends_on   = [google_project_service.api]
}

resource "google_service_account" "deployer" {
  account_id   = "mdp-deployer"
  display_name = "MDP — déploiement depuis GitHub (WIF)"
  depends_on   = [google_project_service.api]
}

# --- BigQuery : ingestion écrit dans raw ; dbt lit raw et écrit ailleurs -------------------------------------------
resource "google_bigquery_dataset_iam_member" "ingest_raw_editor" {
  dataset_id = google_bigquery_dataset.layer["raw"].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingest.email}"
}

resource "google_bigquery_dataset_iam_member" "dbt_raw_viewer" {
  dataset_id = google_bigquery_dataset.layer["raw"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "dbt_editor" {
  for_each   = toset(["staging", "intermediate", "marts"])
  dataset_id = google_bigquery_dataset.layer[each.value].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dbt.email}"
}

resource "google_bigquery_dataset_iam_member" "bi_readers" {
  for_each   = toset(var.bi_readers)
  dataset_id = google_bigquery_dataset.layer["marts"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = each.value
}

# Exécuter des requêtes est un droit de projet, séparé de l'accès aux données.
resource "google_project_iam_member" "job_user" {
  for_each = {
    ingest = google_service_account.ingest.email
    dbt    = google_service_account.dbt.email
  }
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${each.value}"
}

# --- Orchestration -------------------------------------------------------------------------------------------------
resource "google_cloud_run_v2_job_iam_member" "workflow_runs_jobs" {
  for_each = {
    ingest_meta   = google_cloud_run_v2_job.ingest_meta.name
    ingest_google = google_cloud_run_v2_job.ingest_google.name
    dbt           = google_cloud_run_v2_job.dbt.name
  }
  location = var.region
  name     = each.value
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.workflow.email}"
}

# Pour lancer un job qui s'exécute sous un autre compte, l'appelant doit pouvoir « agir en tant que » ce compte.
resource "google_service_account_iam_member" "workflow_acts_as_runtime" {
  for_each           = { ingest = google_service_account.ingest.name, dbt = google_service_account.dbt.name }
  service_account_id = each.value
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.workflow.email}"
}

# Le fournisseur Google n'expose pas d'IAM au niveau d'un workflow : rôle accordé au niveau du projet
# (ce projet ne contient qu'un workflow ; à restreindre par condition IAM s'il en héberge d'autres).
resource "google_project_iam_member" "scheduler_invokes_workflows" {
  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

# --- Déploiement depuis GitHub -------------------------------------------------------------------------------------
resource "google_artifact_registry_repository_iam_member" "deployer_pushes" {
  location   = var.region
  repository = google_artifact_registry_repository.images.repository_id
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_project_iam_member" "deployer_updates_jobs" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.deployer.email}"
}

resource "google_service_account_iam_member" "deployer_acts_as_runtime" {
  for_each           = { ingest = google_service_account.ingest.name, dbt = google_service_account.dbt.name }
  service_account_id = each.value
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.deployer.email}"
}
