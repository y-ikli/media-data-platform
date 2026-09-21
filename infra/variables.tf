variable "project_id" {
  description = "Projet GCP de l'environnement (un projet par environnement)."
  type        = string
}

variable "region" {
  description = "Région des jobs, du workflow et des jeux de données BigQuery."
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Nom de l'environnement, utilisé dans les libellés."
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment doit valoir dev ou prod."
  }
}

variable "github_repository" {
  description = "Dépôt GitHub autorisé à déployer (owner/nom)."
  type        = string
  default     = "y-ikli/media-data-platform"
}

variable "github_allowed_ref" {
  description = "Seule cette référence Git peut s'authentifier auprès de GCP."
  type        = string
  default     = "refs/heads/main"
}

variable "image" {
  description = "Image des jobs. La valeur par défaut est l'image d'exemple de Google : le premier apply fonctionne avant tout build ; le déploiement remplace ensuite l'image (ignorée par Terraform)."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/job:latest"
}

variable "meta_mode" {
  description = "simulated (défaut, aucun secret requis) ou real (identifiants Meta lus dans Secret Manager)."
  type        = string
  default     = "simulated"
  validation {
    condition     = contains(["simulated", "real"], var.meta_mode)
    error_message = "meta_mode doit valoir simulated ou real."
  }
}

variable "lookback_days" {
  description = "Fenêtre glissante ingérée à chaque exécution [J-N, J-1] : absorbe les corrections tardives des plateformes."
  type        = number
  default     = 3
}

variable "schedule_cron" {
  description = "Planification (cron) de l'exécution quotidienne."
  type        = string
  default     = "0 6 * * *"
}

variable "schedule_timezone" {
  type    = string
  default = "Europe/Paris"
}

variable "schedule_paused" {
  description = "Planificateur en pause : vrai par défaut, pour ne rien exécuter avant d'avoir validé un run manuel."
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Destinataire des alertes d'échec. Vide : aucune alerte créée."
  type        = string
  default     = ""
}

variable "bi_readers" {
  description = "Membres IAM (ex. user:x@y.z, group:bi@y.z) autorisés à lire les marts (Looker Studio)."
  type        = list(string)
  default     = []
}

variable "billing_account" {
  description = "Compte de facturation pour un budget d'alerte. Vide : aucun budget."
  type        = string
  default     = ""
}

variable "monthly_budget_eur" {
  type    = number
  default = 10
}

variable "deletion_protection" {
  description = "Protège jobs et jeux de données contre la suppression accidentelle (vrai en prod)."
  type        = bool
  default     = true
}
