#!/bin/bash

echo "===== Crypto Portfolio Manager Cloud Run Deployment via ADK ====="
echo ""

ENV_FILE="trading_assistant/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Environment file '$ENV_FILE' not found."
    echo "Please ensure the .env file exists at trading_assistant/.env"
    exit 1
fi

set -a 
if ! source "$ENV_FILE"; then
    echo "Error: Failed to source environment variables from '$ENV_FILE'."
    set +a
    exit 1
fi
set +a

REQUIRED_VARS=(
    "GOOGLE_CLOUD_PROJECT"
    "GOOGLE_CLOUD_LOCATION"
    "SERVICE_NAME"
    "APP_NAME"
    "AGENT_PATH"
)
MISSING_VARS=0
for VAR_NAME in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR_NAME}" ]; then
        echo "Error: Required environment variable '$VAR_NAME' is not set in '$ENV_FILE'."
        MISSING_VARS=1
    fi
done

if [ "$MISSING_VARS" -eq 1 ]; then
    echo "Please ensure all required variables are set in '$ENV_FILE'."
    exit 1
fi

echo "Deployment Information (from $ENV_FILE):"
echo "  Project ID:    $GOOGLE_CLOUD_PROJECT"
echo "  Region:        $GOOGLE_CLOUD_LOCATION"
echo "  Service Name:  $SERVICE_NAME"
echo "  App Name:      $APP_NAME"
echo "  Agent Path:    $AGENT_PATH"
echo ""

read -p "Proceed with deployment? (y/N): " CONFIRMATION
if [[ "$CONFIRMATION" != "y" && "$CONFIRMATION" != "Y" ]]; then
    echo "Deployment cancelled by user."
    exit 0
fi
echo ""

DEPLOY_CMD=(
    "adk" "deploy" "cloud_run"
    "--project=$GOOGLE_CLOUD_PROJECT"
    "--region=$GOOGLE_CLOUD_LOCATION"
    "--service_name=$SERVICE_NAME"
    "--app_name=$APP_NAME"
    "--with_ui"
    "$AGENT_PATH"
)

echo "Starting deployment, this may take a few minutes..."
echo "Executing command: ${DEPLOY_CMD[*]}"
echo ""

if ! "${DEPLOY_CMD[@]}"; then
    echo "Error: ADK deployment command failed."
    exit 1
fi

echo ""
echo "ADK deployment process finished successfully."
echo "Please check the Google Cloud Console for the status of your Cloud Run service."
