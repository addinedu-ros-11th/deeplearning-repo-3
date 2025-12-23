#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-hybrid-cabinet-481908-u7}"
REGION="${REGION:-asia-northeast3}"
REPO_NAME="${REPO_NAME:-bake-sight-repo}"
SERVICE_NAME="${SERVICE_NAME:-bake-sight-central}"

INSTANCE_CONNECTION_NAME="${INSTANCE_CONNECTION_NAME:-hybrid-cabinet-481908-u7:asia-northeast3:bake-sight}"

# Direct VPC egress (필수: AI 사설 IP 접근)
VPC="${VPC:-default}"
SUBNET="${SUBNET:-default}"  # 리전 default subnet 이름이 다를 수 있음(콘솔에서 확인)

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_EMAIL:-bake-sight-central-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

# Secret Manager secrets
SECRET_ADMIN_KEY="${SECRET_ADMIN_KEY:-BAKE_SIGHT_ADMIN_KEY}"
SECRET_DATABASE_URL="${SECRET_DATABASE_URL:-BAKE_SIGHT_DATABASE_URL}"
SECRET_AI_ADMIN_KEY="${SECRET_AI_ADMIN_KEY:-BAKE_SIGHT_AI_ADMIN_KEY}"

AI_BASE_URL="${AI_BASE_URL:-http://10.178.0.2:9000}"

IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/bake-sight-central:latest"

command -v gcloud >/dev/null 2>&1 || { echo "gcloud not found"; exit 1; }

echo "[0/6] Project: ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}" >/dev/null

echo "[1/6] Build & push image (Cloud Build)"
gcloud builds submit --tag "${IMAGE}"

echo "[2/6] Deploy Cloud Run"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform gen2 \
  --service-account "${SERVICE_ACCOUNT_EMAIL}" \
  --network "${VPC}" \
  --subnet "${SUBNET}" \
  --vpc-egress "private-ranges-only" \
  --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}" \
  --update-secrets "ADMIN_KEY=${SECRET_ADMIN_KEY}:latest,DATABASE_URL=${SECRET_DATABASE_URL}:latest,AI_ADMIN_KEY=${SECRET_AI_ADMIN_KEY}:latest" \
  --update-env-vars "AI_BASE_URL=${AI_BASE_URL},CREATE_TABLES=1,DB_POOL_SIZE=5,DB_MAX_OVERFLOW=2,DB_POOL_RECYCLE=1800" \
  --allow-unauthenticated

echo "[3/6] Print service URL"
SERVICE_URL="$(gcloud run services describe "${SERVICE_NAME}" --region "${REGION}" --format='value(status.url)')"
echo "Service URL: ${SERVICE_URL}"

echo "[4/6] IMPORTANT: 테이블 생성 확인 후 CREATE_TABLES 끄기"
echo "  gcloud run services update ${SERVICE_NAME} --region ${REGION} --update-env-vars CREATE_TABLES=0"

echo "[5/6] IAM checklist"
echo "  - Cloud SQL: roles/cloudsql.client for ${SERVICE_ACCOUNT_EMAIL}"
echo "  - Secrets: roles/secretmanager.secretAccessor for ${SERVICE_ACCOUNT_EMAIL}"

echo "[6/6] Artifact Registry image"
echo "  ${IMAGE}"
