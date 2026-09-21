locals {
  alerts_enabled = var.alert_email != ""
}

resource "google_monitoring_notification_channel" "email" {
  count        = local.alerts_enabled ? 1 : 0
  display_name = "MDP — alertes (${var.environment})"
  type         = "email"
  labels       = { email_address = var.alert_email }
  depends_on   = [google_project_service.api]
}

# Une exécution du workflow quotidien a échoué (ingestion invalide, test dbt en échec, API indisponible…).
resource "google_monitoring_alert_policy" "workflow_failed" {
  count        = local.alerts_enabled ? 1 : 0
  display_name = "MDP — exécution quotidienne en échec (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Exécution FAILED"
    condition_threshold {
      filter          = "resource.type = \"workflows.googleapis.com/Workflow\" AND resource.labels.workflow_id = \"${google_workflows_workflow.daily.name}\" AND metric.type = \"workflows.googleapis.com/finished_execution_count\" AND metric.labels.status = \"FAILED\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email[0].id]

  documentation {
    mime_type = "text/markdown"
    content   = "Voir les journaux du workflow `mdp-daily` et du job en échec. Procédure : docs/runbook.md."
  }
}

# Aucune exécution réussie depuis 26 h : le planificateur est en pause, cassé, ou le workflow ne finit plus.
resource "google_monitoring_alert_policy" "workflow_stale" {
  count        = local.alerts_enabled && !var.schedule_paused ? 1 : 0
  display_name = "MDP — aucune exécution réussie depuis 26 h (${var.environment})"
  combiner     = "OR"

  conditions {
    display_name = "Pas de SUCCEEDED"
    condition_absent {
      filter   = "resource.type = \"workflows.googleapis.com/Workflow\" AND resource.labels.workflow_id = \"${google_workflows_workflow.daily.name}\" AND metric.type = \"workflows.googleapis.com/finished_execution_count\" AND metric.labels.status = \"SUCCEEDED\""
      duration = "93600s"

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email[0].id]
}

resource "google_billing_budget" "monthly" {
  count           = var.billing_account != "" ? 1 : 0
  billing_account = var.billing_account
  display_name    = "MDP — budget mensuel (${var.environment})"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "EUR"
      units         = tostring(var.monthly_budget_eur)
    }
  }

  threshold_rules { threshold_percent = 0.5 }
  threshold_rules { threshold_percent = 0.9 }
  threshold_rules { threshold_percent = 1.0 }
}
