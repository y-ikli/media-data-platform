# Workload Identity Federation : GitHub Actions s'authentifie par jeton OIDC éphémère, sans clé JSON.
# Seuls ce dépôt ET cette référence Git peuvent obtenir le compte de déploiement.
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "mdp-github"
  display_name              = "GitHub Actions"
  depends_on                = [google_project_service.api]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github"
  display_name                       = "GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
    "attribute.ref"        = "assertion.ref"
  }

  # Sans cette condition, n'importe quel dépôt GitHub pourrait tenter l'usurpation.
  attribute_condition = "assertion.repository == \"${var.github_repository}\" && assertion.ref == \"${var.github_allowed_ref}\""

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_member" "github_impersonates_deployer" {
  service_account_id = google_service_account.deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repository}"
}
