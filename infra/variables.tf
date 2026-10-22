variable "project_id" {
  description = "Identifiant du projet Google Cloud."
  type        = string
}

variable "region" {
  description = "Région de toutes les ressources. Celle d'un dataset BigQuery ne se change plus après sa création."
  type        = string
  default     = "europe-west1"
}

variable "dataset_prefix" {
  description = "Préfixe des datasets BigQuery (ads_raw, ads_staging, ads_marts)."
  type        = string
  default     = "ads"
}

variable "github_repository" {
  description = "Dépôt GitHub autorisé à déployer (propriétaire/nom)."
  type        = string
  default     = "y-ikli/media-data-platform"
}

variable "meta_mode" {
  description = "Mode du job d'ingestion Meta Ads : simulated, ou real avec le jeton dans Secret Manager."
  type        = string
  default     = "simulated"

  validation {
    condition     = contains(["simulated", "real"], var.meta_mode)
    error_message = "meta_mode doit valoir simulated ou real."
  }
}

variable "meta_ads_account_id" {
  description = "Compte publicitaire Meta (act_…), requis si meta_mode = real. À mettre dans terraform.tfvars."
  type        = string
  default     = ""
}

variable "initial_image" {
  description = "Image de départ des jobs ; ensuite, c'est la CI qui déploie l'image du pipeline."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/job:latest"
}

variable "lookback_days" {
  description = "Jours retraités par chaque ingestion quotidienne (corrections tardives des plateformes)."
  type        = number
  default     = 7
}

variable "schedule" {
  description = "Heure de lancement du pipeline, au format cron."
  type        = string
  default     = "0 7 * * *"
}

variable "time_zone" {
  description = "Fuseau horaire de schedule."
  type        = string
  default     = "Europe/Paris"
}
