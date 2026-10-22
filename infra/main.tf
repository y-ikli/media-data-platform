provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  labels = {
    projet   = "media-data-platform"
    gere_par = "terraform"
  }

  # Adresse des images du pipeline dans Artifact Registry.
  image_repository = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}/adsdata"
}
