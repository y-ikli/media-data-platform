# Trois jobs Cloud Run, une seule image : deux ingestions et la transformation dbt.
#
# L'image est déployée par la CI (gcloud run jobs update --image) : Terraform crée les jobs avec
# l'image de départ puis ignore ce champ, sinon chaque `apply` remettrait l'ancienne version.
locals {
  ingest_jobs = {
    google_ads = { mode = "simulated" }
    meta_ads   = { mode = var.meta_mode }
  }

  job_names = merge(
    { for source, _ in local.ingest_jobs : source => "ingest-${replace(source, "_", "-")}" },
    { transform = "dbt-build" },
  )

  common_env = {
    GCP_PROJECT_ID = var.project_id
    BQ_LOCATION    = var.region
    BQ_RAW_DATASET = google_bigquery_dataset.layer["raw"].dataset_id
  }
}

resource "google_cloud_run_v2_job" "ingest" {
  for_each = local.ingest_jobs

  name                = local.job_names[each.key]
  location            = var.region
  labels              = local.labels
  deletion_protection = false

  template {
    task_count = 1

    template {
      service_account = google_service_account.pipeline["ingestion"].email
      timeout         = "900s"
      max_retries     = 1

      containers {
        image   = var.initial_image
        command = ["adsdata-ingest"]
        args = [
          "--source", each.key,
          "--mode", each.value.mode,
          "--lookback-days", tostring(var.lookback_days),
        ]

        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }

        dynamic "env" {
          for_each = merge(
            local.common_env,
            each.key == "meta_ads" && each.value.mode == "real" ? { META_ADS_ACCOUNT_ID = var.meta_ads_account_id } : {},
          )
          content {
            name  = env.key
            value = env.value
          }
        }

        dynamic "env" {
          for_each = each.key == "meta_ads" && each.value.mode == "real" ? [1] : []
          content {
            name = "META_ADS_ACCESS_TOKEN"
            value_source {
              secret_key_ref {
                secret  = google_secret_manager_secret.meta_ads_access_token.secret_id
                version = "latest"
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]

    precondition {
      condition     = !(each.key == "meta_ads" && each.value.mode == "real" && var.meta_ads_account_id == "")
      error_message = "meta_mode = \"real\" exige meta_ads_account_id dans terraform.tfvars."
    }
  }

  depends_on = [
    google_project_service.enabled,
    google_secret_manager_secret_iam_member.ingestion_reads_meta_token,
  ]
}

resource "google_cloud_run_v2_job" "transform" {
  name                = local.job_names["transform"]
  location            = var.region
  labels              = local.labels
  deletion_protection = false

  template {
    task_count = 1

    template {
      service_account = google_service_account.pipeline["transform"].email
      timeout         = "1800s"
      max_retries     = 0

      containers {
        image   = var.initial_image
        command = ["dbt"]
        args    = ["build", "--target", "prod"]

        resources {
          limits = { cpu = "1", memory = "2Gi" }
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

  depends_on = [google_project_service.enabled]
}
