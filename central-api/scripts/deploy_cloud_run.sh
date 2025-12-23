#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-REPLACE_ME}"
REGION="${REGION:-asia-northeast3}"          # 예: asia-northeast3 (서울)
REPO_NAME="${REPO_NAME:-REPLACE_ME}"         # Artifact Registry repo
SERVICE_NAME="${SERVICE_NAME:-smart-cafe-api}"

# Cloud SQL instance connection name: project:region:instance-id
INSTANCE_CONNECTION_NAME="${INSTANCE_CONNECTION_NAME:-REPLACE_ME}"

# Service Account (recommended)
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-smart-cafe-run@${PROJECT_ID}.iam.gserviceaccount.com}"

# Secret Manager secrets
SECRET_ADMIN_KEY="${SECRET_ADMIN_KEY:-BAKE_SIGHT_ADMIN_KEY}"
SECRET_DATABASE_URL="${SECRET_DATABASE_URL:-BAKE_SIGHT_DATABASE_URL}"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/smart-cafe-api:latest"

command -v gcloud >/dev/null 2>&1 || { echo "gcloud not found"; exit 1; }

echo "[0/5] Project: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}" >/dev/null

echo "[1/5] Build & push image (Cloud Build)"
gcloud builds submit --tag "${IMAGE}"

echo "[2/5] Deploy Cloud Run"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --service-account "${SERVICE_ACCOUNT_EMAIL}" \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --update-secrets "ADMIN_KEY=${SECRET_ADMIN_KEY}:latest,DATABASE_URL=${SECRET_DATABASE_URL}:latest" \
  --update-env-vars "CREATE_TABLES=1,DB_POOL_SIZE=5,DB_MAX_OVERFLOW=2,DB_POOL_RECYCLE=1800" \
  --allow-unauthenticated

echo "[3/5] Print service URL"
SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')"
echo "Service URL: ${SERVICE_URL}"

echo "[4/5] IMPORTANT: 테이블 생성 확인 후 CREATE_TABLES 끄기"
echo "  gcloud run services update ${SERVICE_NAME} --region ${REGION} --update-env-vars CREATE_TABLES=0"

echo "[5/5] Permission checklist"
echo "  - Cloud SQL: roles/cloudsql.client on project for ${SERVICE_ACCOUNT_EMAIL}"
echo "  - Secrets: roles/secretmanager.secretAccessor on BAKE_SIGHT_ADMIN_KEY and BAKE_SIGHT_DATABASE_URL for ${SERVICE_ACCOUNT_EMAIL}"
