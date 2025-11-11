#############################################
# miAsistenciaIA - Infraestructura GCP (Terraform)
#############################################

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5.0"
}

#############################################
# VARIABLES
#############################################

variable "gcp_project_id" {
  description = "ID del proyecto GCP donde se desplegará miAsistenciaIA"
  type        = string
  default     = "ia-marketing-digita" # ⚠️ Cambia si usas otro proyecto
}

variable "gcp_region" {
  description = "Región GCP para recursos (Cloud Run, Scheduler)"
  type        = string
  default     = "us-central1" # compatible con Cloud Scheduler
}

variable "bq_location" {
  description = "Ubicación del dataset de BigQuery"
  type        = string
  default     = "US"
}

variable "ads_customer_id" {
  description = "Login Customer ID de Google Ads (sin guiones)"
  type        = string
  default     = "1838759325"
}

variable "secrets" {
  description = "Lista de secretos requeridos por el pipeline"
  type        = list(string)
  default     = [
    "ADS_DEVELOPER_TOKEN",
    "ADS_CLIENT_ID",
    "ADS_CLIENT_SECRET",
    "ADS_REFRESH_TOKEN",
    "GMAIL_USER",
    "GMAIL_APP_PASSWORD",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID"
  ]
}

#############################################
# PROVEEDOR
#############################################

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

#############################################
# 1. HABILITAR APIS
#############################################

resource "google_project_service" "apis" {
  for_each = toset([
    "googleads.googleapis.com",
    "bigquery.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "aiplatform.googleapis.com",
    "cloudbuild.googleapis.com"
  ])

  project                    = var.gcp_project_id
  service                    = each.key
  disable_dependent_services = true
  disable_on_destroy         = false
}

#############################################
# 2. SERVICE ACCOUNT
#############################################

resource "google_service_account" "mi_asistencia_sa" {
  account_id   = "mi-asistenciaia-sa"
  display_name = "Service Account for miAsistenciaIA Pipeline"
  project      = var.gcp_project_id
  depends_on   = [google_project_service.apis]
}

#############################################
# 3. ROLES IAM
#############################################

resource "google_project_iam_member" "sa_roles" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/secretmanager.secretAccessor",
    "roles/aiplatform.user",
    "roles/storage.objectAdmin",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/run.invoker"
  ])
  project = var.gcp_project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.mi_asistencia_sa.email}"
}

#############################################
# 4. DATASET BIGQUERY
#############################################

resource "google_bigquery_dataset" "dataset" {
  dataset_id  = "mi_asistenciaia"
  location    = var.bq_location
  description = "Dataset principal de miAsistenciaIA"
  project     = var.gcp_project_id
  depends_on  = [google_project_service.apis["bigquery.googleapis.com"]]
}

#############################################
# 5. SECRET MANAGER
#############################################

resource "google_secret_manager_secret" "secret" {
  for_each  = toset(var.secrets)
  project   = var.gcp_project_id
  secret_id = each.key

  # --- CORRECCIÓN DE SINTAXIS ---
  replication {
    auto {}
  }

  depends_on = [google_project_service.apis["secretmanager.googleapis.com"]]
}

#############################################
# 6. CLOUD RUN JOB
#############################################

resource "google_cloud_run_v2_job" "pipeline_job" {
  name     = "mi-asistenciaia-pipeline"
  location = var.gcp_region
  project  = var.gcp_project_id

  template {
    template {
      service_account = google_service_account.mi_asistencia_sa.email
      timeout         = "3600s"

      containers {
        image = "gcr.io/${var.gcp_project_id}/mi-asistenciaia:latest"
        env {
          name  = "PROJECT_ID"
          value = var.gcp_project_id
        }
        env {
          name  = "DATASET_ID"
          value = google_bigquery_dataset.dataset.dataset_id
        }
        env {
          name  = "ADS_LOGIN_CUSTOMER_ID"
          value = var.ads_customer_id
        }
        env {
          name  = "PIPELINE_STEP"
          value = "FULL_E2E"
        }
      }
    }
  }

  depends_on = [
    google_project_iam_member.sa_roles,
    google_bigquery_dataset.dataset
  ]
}

#############################################
# 7. CLOUD SCHEDULER JOB
#############################################

resource "google_cloud_scheduler_job" "daily_run" {
  name        = "mi-asistenciaia-daily-trigger"
  region      = var.gcp_region
  project     = var.gcp_project_id
  schedule    = "0 7 * * *" # 7 AM Santiago Time
  time_zone   = "America/Santiago"
  description = "Trigger diario del pipeline miAsistenciaIA"

  http_target {
    # --- CORRECCIÓN DE URI ---
    uri = "https://run.googleapis.com/v2/projects/${var.gcp_project_id}/locations/${var.gcp_region}/jobs/${google_cloud_run_v2_job.pipeline_job.name}:run"
    http_method = "POST"
    oauth_token {
      service_account_email = google_service_account.mi_asistencia_sa.email
    }
  }

  depends_on = [google_cloud_run_v2_job.pipeline_job]
}

#############################################
# OUTPUTS
#############################################

output "service_account_email" {
  description = "Cuenta de servicio usada por Cloud Run"
  value       = google_service_account.mi_asistencia_sa.email
}

output "cloud_run_job_uri" {
  description = "Endpoint de ejecución del Cloud Run Job (no es el URI del recurso)"
  # --- CORRECCIÓN DE URI ---
  value = "https://run.googleapis.com/v2/projects/${var.gcp_project_id}/locations/${var.gcp_region}/jobs/${google_cloud_run_v2_job.pipeline_job.name}"
}

output "scheduler_job_name" {
  description = "Nombre del Job de Cloud Scheduler"
  value       = google_cloud_scheduler_job.daily_run.name
}

output "bigquery_dataset" {
  description = "Nombre del Dataset creado en BigQuery"
  value       = google_bigquery_dataset.dataset.dataset_id
}	