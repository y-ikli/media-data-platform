terraform {
  required_version = ">= 1.6"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # L'état est stocké dans un bucket GCS créé une fois par bootstrap.sh :
  #   terraform init -backend-config="bucket=<projet>-tfstate"
  backend "gcs" {
    prefix = "media-data-platform"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
