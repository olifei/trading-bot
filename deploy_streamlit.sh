#!/bin/bash

echo "===== Fixed Streamlit Deployment Script ====="
echo ""

ENV_FILE="trading_assistant/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
REPO_NAME="docker-images"
SERVICE_NAME="${SERVICE_NAME:-trading-bot}"
STREAMLIT_SERVICE_NAME="${SERVICE_NAME}-frontend"

IMAGE_NAME="${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${STREAMLIT_SERVICE_NAME}"

echo "Deployment Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Location: $LOCATION"
echo "  Service: $STREAMLIT_SERVICE_NAME"
echo "  Image: $IMAGE_NAME"
echo ""

read -p "Proceed with deployment? (y/N): " CONFIRM
if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
    echo "Deployment cancelled."
    exit 0
fi

echo "Building Docker image..."
if gcloud builds submit --tag "$IMAGE_NAME" . --project="$PROJECT_ID"; then
    echo "Build successful!"
else
    echo "Build failed!"
    exit 1
fi

echo "Deploying to Cloud Run..."
if gcloud run deploy "$STREAMLIT_SERVICE_NAME" \
    --image="$IMAGE_NAME" \
    --platform=managed \
    --region="$LOCATION" \
    --allow-unauthenticated \
    --project="$PROJECT_ID"; then
    echo "Deployment successful!"
else
    echo "Deployment failed!"
    exit 1
fi
