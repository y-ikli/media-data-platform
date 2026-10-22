# Le jeton Meta est un secret : Terraform crée le coffre, jamais la valeur (elle finirait dans
# le state). La valeur s'ajoute à la main :
#   gcloud secrets versions add meta-ads-access-token --data-file=-
resource "google_secret_manager_secret" "meta_ads_access_token" {
  secret_id = "meta-ads-access-token"
  labels    = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.enabled]
}

resource "google_secret_manager_secret_iam_member" "ingestion_reads_meta_token" {
  secret_id = google_secret_manager_secret.meta_ads_access_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.pipeline["ingestion"].member
}
