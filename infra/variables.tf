variable "project_id" {
  type        = string
  description = "Target Google Cloud project id."
}

variable "region" {
  type        = string
  description = "Region for Cloud Run and Artifact Registry."
  default     = "us-central1"
}

variable "firestore_location" {
  type        = string
  description = "Firestore location (multi-region such as nam5/eur3, or a region)."
  default     = "nam5"
}

variable "database_id" {
  type        = string
  description = "Firestore database id (matches FIRESTORE_DATABASE_ID in .env)."
  default     = "trading-bot-db"
}

variable "service_name" {
  type        = string
  description = "Cloud Run service name / base name for related resources."
  default     = "trading-bot"
}

variable "container_image" {
  type        = string
  description = "Fully-qualified container image URI to deploy to Cloud Run."
}

variable "genai_use_vertexai" {
  type        = string
  description = "Value for GOOGLE_GENAI_USE_VERTEXAI (1 to use Vertex AI)."
  default     = "1"
}

variable "allow_unauthenticated" {
  type        = bool
  description = "Whether to allow public (unauthenticated) access to the service."
  default     = false
}
