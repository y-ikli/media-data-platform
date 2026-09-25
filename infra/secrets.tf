# Conteneurs de secrets uniquement : AUCUNE valeur n'est écrite par Terraform (elle finirait dans l'état).
# Ajouter la valeur hors bande :  printf '%s' "$TOKEN" | gcloud secrets versions add mdp-meta-ads-access-token --data-file=-
locals {
  meta_secrets = toset(["app-id", "app-secret", "access-token", "account-id"])
}

resource "google_secret_manager_secret" "meta" {
  for_each  = local.meta_secrets
  secret_id = "mdp-meta-ads-${each.value}"
  labels    = local.labels

  replication {
    auto {}
  }

  depends_on = [google_project_service.api]
}

resource "google_secret_manager_secret_iam_member" "ingest_reads_meta" {
  for_each  = local.meta_secrets
  secret_id = google_secret_manager_secret.meta[each.value].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ingest.email}"
}
