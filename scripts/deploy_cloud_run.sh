#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-asia-northeast3}"
SERVICE_NAME="${SERVICE_NAME:-ai-arena-web}"
REPOSITORY="${REPOSITORY:-ai-arena}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "PROJECT_ID is required. Example: PROJECT_ID=my-gcp-project scripts/deploy_cloud_run.sh"
  exit 1
fi

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:$(git rev-parse --short HEAD)"

echo "[1/4] Enable required services"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$PROJECT_ID"

echo "[2/4] Ensure Artifact Registry repository exists"
if ! gcloud artifacts repositories describe "$REPOSITORY" --location "$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPOSITORY" \
    --repository-format=docker \
    --location "$REGION" \
    --description="AI Arena container repository" \
    --project "$PROJECT_ID"
fi

echo "[3/4] Build and push image"
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID"

echo "[4/4] Deploy to Cloud Run"
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --project "$PROJECT_ID"

echo "Deployed: $(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format='value(status.url)')"
