resource "google_artifact_registry_repository" "images" {
  repository_id = "pipeline"
  location      = var.region
  format        = "DOCKER"
  description   = "Images du pipeline (ingestion et dbt)."
  labels        = local.labels

  # Garder les 5 dernières images, supprimer les autres après 7 jours : le stockage reste gratuit.
  cleanup_policy_dry_run = false
  cleanup_policies {
    id     = "garder-les-5-dernieres"
    action = "KEEP"
    most_recent_versions {
      keep_count = 5
    }
  }
  cleanup_policies {
    id     = "supprimer-les-anciennes"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "604800s"
    }
  }

  depends_on = [google_project_service.enabled]
}
