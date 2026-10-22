# Versions de Terraform et du provider Google.
# Le fichier .terraform.lock.hcl, créé par `terraform init`, fixe la version exacte : il est versionné.
terraform {
  required_version = ">= 1.10"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.7"
    }
  }
}
