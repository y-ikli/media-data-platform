# Jeux de données de l'environnement. Les tables raw sont créées par `mdp-ingest` (schéma déclaré dans le code) ;
# les modèles dbt créent leurs tables dans staging / intermediate / marts.
locals {
  datasets = {
    raw          = "mdp_raw"
    staging      = "mdp_staging"
    intermediate = "mdp_intermediate"
    marts        = "mdp_marts"
    # Schéma par défaut de la cible dbt `prod` (profiles.yml) : dbt le vérifie au démarrage.
    default = "mdp"
  }
  labels = {
    app         = "media-data-platform"
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "google_bigquery_dataset" "layer" {
  for_each                   = local.datasets
  dataset_id                 = each.value
  location                   = var.region
  description                = "Media Data Platform — couche ${each.key}"
  labels                     = local.labels
  delete_contents_on_destroy = false

  depends_on = [google_project_service.api]
}
