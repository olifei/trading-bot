# Infrastructure (Terraform)

Infrastructure-as-Code for provisioning the trading assistant on Google Cloud.

## What it creates

- Enables required APIs (Cloud Run, Firestore, Vertex AI, Artifact Registry)
- A **Firestore** database (`database_id`)
- A least-privilege **service account** (`roles/datastore.user`, `roles/aiplatform.user`)
- An **Artifact Registry** Docker repository
- A **Cloud Run** service, with config injected as env vars that match the
  single-source `.env` contract (`GOOGLE_CLOUD_PROJECT`, `FIRESTORE_DATABASE_ID`,
  `GOOGLE_CLOUD_LOCATION`, `GOOGLE_GENAI_USE_VERTEXAI`)

## Usage

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # then edit values
terraform init
terraform plan
terraform apply
```

Build & push the image before `apply` (or update `container_image` afterwards):

```bash
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT/trading-bot/trading-bot:latest"
```

> For real deployments configure a remote state backend (e.g. a GCS bucket)
> instead of local state.
