locals {
  # Une entrée par couche : la clé donne le nom du dataset, la valeur sa description.
  datasets = {
    raw     = "Données brutes des plateformes publicitaires, telles qu'extraites."
    staging = "Données typées et dédupliquées, une table par source (dbt)."
    marts   = "Tables d'analyse lues par Looker Studio (dbt)."
  }
}

resource "google_bigquery_dataset" "layer" {
  for_each = local.datasets

  dataset_id  = "${var.dataset_prefix}_${each.key}"
  location    = var.region
  description = each.value
  labels      = local.labels

  # Refuse de supprimer un dataset qui contient encore des tables.
  delete_contents_on_destroy = false

  depends_on = [google_project_service.enabled]
}
