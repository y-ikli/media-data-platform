# Trois jobs Cloud Run, une seule image : ingestion Meta, ingestion Google, transformations dbt.
# Les jobs tournent sous leur propre compte de service ; ils ne partagent aucun droit.
locals {
  common_env = {
    GCP_PROJECT_ID = var.project_id
    BQ_LOCATION    = var.region
    BQ_RAW_DATASET = local.datasets.raw
  }
  meta_secret_env = {
    META_ADS_APP_ID       = "app-id"
    META_ADS_APP_SECRET   = "app-secret"
    META_ADS_ACCESS_TOKEN = "access-token"
    META_ADS_ACCOUNT_ID   = "account-id"
  }
}

resource "google_cloud_run_v2_job" "ingest_meta" {
  name                = "mdp-ingest-meta"
  location            = var.region
  labels              = local.labels
  deletion_protection = var.deletion_protection

  template {
    template {
      service_account = google_service_account.ingest.email
      max_retries     = 1
      timeout         = "1800s"

      containers {
        image   = var.image
        command = ["mdp-ingest"]
        args    = ["--source", "meta_ads", "--mode", var.meta_mode, "--lookback-days", tostring(var.lookback_days)]

        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }

        dynamic "env" {
          for_each = local.common_env
          content {
            name  = env.key
            value = env.value
          }
        }

        # Les identifiants ne sont montés qu'en mode réel : en simulé, aucun secret n'est lu.
        dynamic "env" {
          for_each = var.meta_mode == "real" ? local.meta_secret_env : {}
          content {
            name = env.key
            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.meta[env.value].secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    # L'image est mise à jour par le pipeline de déploiement, pas par Terraform.
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_project_service.api]
}

resource "google_cloud_run_v2_job" "ingest_google" {
  name                = "mdp-ingest-google"
  location            = var.region
  labels              = local.labels
  deletion_protection = var.deletion_protection

  template {
    template {
      service_account = google_service_account.ingest.email
      max_retries     = 1
      timeout         = "1800s"

      containers {
        image   = var.image
        command = ["mdp-ingest"]
        # Google Ads n'a pas d'extraction réelle : toujours simulé (l'option `real` échoue par conception).
        args = ["--source", "google_ads", "--mode", "simulated", "--lookback-days", tostring(var.lookback_days)]

        resources {
          limits = { cpu = "1", memory = "512Mi" }
        }

        dynamic "env" {
          for_each = local.common_env
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_project_service.api]
}

resource "google_cloud_run_v2_job" "dbt" {
  name                = "mdp-dbt"
  location            = var.region
  labels              = local.labels
  deletion_protection = var.deletion_protection

  template {
    template {
      service_account = google_service_account.dbt.email
      max_retries     = 0 # un échec de test dbt n'est pas transitoire : inutile de le rejouer
      timeout         = "1800s"

      containers {
        image   = var.image
        command = ["dbt"]
        args    = ["build", "--project-dir", "dbt/mdp", "--profiles-dir", "dbt/mdp"]

        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }

        dynamic "env" {
          for_each = merge(local.common_env, { DBT_TARGET = "prod" })
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_project_service.api]
}
