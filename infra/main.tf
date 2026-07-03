locals {
  services = [
    "run.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "artifactregistry.googleapis.com",
  ]
}

# Enable the APIs the assistant depends on.
resource "google_project_service" "enabled" {
  for_each = toset(local.services)

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# Firestore database backing the mock trading data.
resource "google_firestore_database" "db" {
  project     = var.project_id
  name        = var.database_id
  location_id = var.firestore_location
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.enabled]
}

# Dedicated runtime service account (least privilege).
resource "google_service_account" "app" {
  project      = var.project_id
  account_id   = "${var.service_name}-sa"
  display_name = "Trading Bot Cloud Run runtime"
}

resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.app.email}"
}

# Container registry for the built image.
resource "google_artifact_registry_repository" "repo" {
  project       = var.project_id
  location      = var.region
  repository_id = var.service_name
  format        = "DOCKER"
  description   = "Trading bot container images"

  depends_on = [google_project_service.enabled]
}

# The Cloud Run service. Configuration is injected as env vars so it matches the
# single-source .env contract (GOOGLE_CLOUD_PROJECT / FIRESTORE_DATABASE_ID).
resource "google_cloud_run_v2_service" "app" {
  project  = var.project_id
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.app.email

    containers {
      image = var.container_image

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GOOGLE_CLOUD_LOCATION"
        value = var.region
      }
      env {
        name  = "FIRESTORE_DATABASE_ID"
        value = var.database_id
      }
      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = var.genai_use_vertexai
      }
    }
  }

  depends_on = [google_project_service.enabled]
}

# Optionally expose the service publicly.
resource "google_cloud_run_v2_service_iam_member" "public" {
  count = var.allow_unauthenticated ? 1 : 0

  project  = var.project_id
  name     = google_cloud_run_v2_service.app.name
  location = google_cloud_run_v2_service.app.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
