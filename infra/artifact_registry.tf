resource "google_artifact_registry_repository" "images" {
  repository_id = "mdp"
  location      = var.region
  format        = "DOCKER"
  description   = "Image des jobs Media Data Platform"
  labels        = local.labels

  # Garde les 10 dernières images ; supprime les plus vieilles que 30 jours au-delà.
  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }
  cleanup_policies {
    id     = "delete-old"
    action = "DELETE"
    condition {
      older_than = "2592000s"
    }
  }

  depends_on = [google_project_service.api]
}
