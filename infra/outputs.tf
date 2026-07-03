output "service_url" {
  description = "Public URL of the deployed Cloud Run service."
  value       = google_cloud_run_v2_service.app.uri
}

output "service_account_email" {
  description = "Runtime service account used by the service."
  value       = google_service_account.app.email
}

output "firestore_database_id" {
  description = "Firestore database id."
  value       = google_firestore_database.db.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository for container images."
  value       = google_artifact_registry_repository.repo.name
}
