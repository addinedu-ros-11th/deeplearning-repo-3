# End-to-End 배포 Runbook (배포용)
목표 아키텍처(서울):
- Central API: Cloud Run (asia-northeast3)
- DB: Cloud SQL for MySQL (asia-northeast3)
- AI Inference: Compute Engine GPU VM 1대 (asia-northeast3-*), **External IP 없음**
- Storage: GCS (선택: tray/cctv/models)

설계 의도:
- Central은 “상태/거래 데이터”의 Source of Truth
- AI VM은 GPU/모델 로딩을 담당(Compute Engine)
- Central → AI는 **VPC 내부 사설 IP 호출**(방화벽으로 최소 허용)

---

## 0) 사전 준비
- Billing 활성화
- `gcloud` 로그인 및 프로젝트 선택
- 조직 정책에 따라 리소스 생성 권한 필요

---

## 1) 변수(한 번만 정하기)
```bash
export PROJECT_ID="<PROJECT_ID>"
export REGION="asia-northeast3"
export ZONE="asia-northeast3-a"

export REPO="bake_sight-repo"

# 네트워크
export VPC="bake_sight-vpc"
export SUBNET="bake_sight-subnet"
export SUBNET_RANGE="10.10.0.0/24"

# 서비스/VM
export CENTRAL_SERVICE="bake_sight-central"
export CENTRAL_NET_TAG="central-run"     # Cloud Run 네트워크 태그 (방화벽에 사용)
export AI_VM="bake_sight-ai-01"
export AI_PORT="9000"

# Cloud SQL
export SQL_INSTANCE="bake_sight-mysql"
export DB_NAME="bake_sight_demo"
export DB_USER="demo"
export DB_PASS="<PASSWORD>"
export INSTANCE_CONNECTION_NAME="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
```

---

## 2) API 활성화
```bash
gcloud config set project "${PROJECT_ID}"

gcloud services enable   run.googleapis.com   cloudbuild.googleapis.com   artifactregistry.googleapis.com   sqladmin.googleapis.com   secretmanager.googleapis.com   compute.googleapis.com
```

---

## 3) Artifact Registry 생성
```bash
gcloud artifacts repositories create "${REPO}"   --repository-format=docker   --location "${REGION}"   --description "Smart Cafe images"
```

---

## 4) VPC/Subnet 생성
Cloud Run을 VPC/Subnet에 직접 붙여서(Direct VPC egress) AI VM 사설 IP로 호출합니다.
```bash
gcloud compute networks create "${VPC}" --subnet-mode=custom

gcloud compute networks subnets create "${SUBNET}"   --network "${VPC}"   --region "${REGION}"   --range "${SUBNET_RANGE}"
```

---

## 5) GCS 버킷(선택이지만 권장)
```bash
export BUCKET_TRAY="${PROJECT_ID}-smartcafe-tray"
export BUCKET_CCTV="${PROJECT_ID}-smartcafe-cctv"
export BUCKET_MODELS="${PROJECT_ID}-smartcafe-models"

gsutil mb -l "${REGION}" "gs://${BUCKET_TRAY}"
gsutil mb -l "${REGION}" "gs://${BUCKET_CCTV}"
gsutil mb -l "${REGION}" "gs://${BUCKET_MODELS}"
```

---

## 6) Cloud SQL(MySQL) 생성
콘솔에서 생성해도 됩니다(권장). 생성 후 아래 값이 준비되어야 합니다.
- `INSTANCE_CONNECTION_NAME` (project:region:instance)
- DB name/user/password

---

## 7) 서비스 계정(IAM) 권장
### 7.1 Central(Cloud Run) 전용 SA
```bash
export CENTRAL_SA="central-run@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud iam service-accounts create central-run --display-name "central cloud run"

gcloud projects add-iam-policy-binding "${PROJECT_ID}"   --member "serviceAccount:${CENTRAL_SA}"   --role "roles/cloudsql.client"

# (선택) Central에서 GCS 업로드/다운로드를 할 경우
gcloud projects add-iam-policy-binding "${PROJECT_ID}"   --member "serviceAccount:${CENTRAL_SA}"   --role "roles/storage.objectAdmin"
```

### 7.2 AI VM 서비스 계정(선택)
AI VM에서 GCS 다운로드(모델/임베딩)를 할 계획이면 VM 서비스 계정에 `storage.objectViewer` 이상을 주세요.

---

## 8) Secret Manager
```bash
echo -n "<CENTRAL_ADMIN_KEY>" | gcloud secrets create BAKE_SIGHT_ADMIN_KEY --data-file=-
echo -n "<AI_ADMIN_KEY>"      | gcloud secrets create BAKE_SIGHT_AI_ADMIN_KEY --data-file=-

DATABASE_URL="mysql+pymysql://${DB_USER}:${DB_PASS}@/${DB_NAME}?unix_socket=/cloudsql/${INSTANCE_CONNECTION_NAME}&charset=utf8mb4"
echo -n "${DATABASE_URL}"     | gcloud secrets create BAKE_SIGHT_DATABASE_URL --data-file=-
```

---

## 9) AI GPU VM 생성 및 기동
### 9.1 GPU VM 생성(DLVM 이미지 권장)
DLVM 이미지 family는 Google이 관리하는 Deep Learning VM 이미지로, GPU 드라이버/런타임 구성이 수월합니다.

```bash
IMAGE_FAMILY="common-cu128-ubuntu-2204-nvidia-570"
IMAGE_PROJECT="deeplearning-platform-release"

gcloud compute instances create "${AI_VM}"   --zone "${ZONE}"   --subnet "${SUBNET}"   --no-address   --machine-type "n1-standard-4"   --accelerator "type=nvidia-tesla-t4,count=1"   --maintenance-policy TERMINATE   --restart-on-failure   --image-family "${IMAGE_FAMILY}"   --image-project "${IMAGE_PROJECT}"   --boot-disk-size "100GB"   --tags "ai-infer"
```

GPU 확인:
```bash
gcloud compute ssh "${AI_VM}" --zone "${ZONE}" --command "nvidia-smi"
```

### 9.2 방화벽(Cloud Run 네트워크 태그만 허용)
```bash
gcloud compute firewall-rules create allow-ai-from-central-run   --network "${VPC}"   --direction INGRESS   --action ALLOW   --rules "tcp:${AI_PORT}"   --source-tags "${CENTRAL_NET_TAG}"   --target-tags "ai-infer"   --priority 900
```

### 9.3 AI 코드 업로드/설치(systemd)
로컬(레포 루트)에서:
```bash
gcloud compute scp --recurse ./ai-inference "${AI_VM}:/opt/ai-inference" --zone "${ZONE}"
```

VM에서:
```bash
gcloud compute ssh "${AI_VM}" --zone "${ZONE}"

cd /opt/ai-inference
sudo bash scripts/install_ai.sh

# 환경 파일
sudo tee /etc/ai-inference.env >/dev/null <<EOF
AI_ADMIN_KEY=<AI_ADMIN_KEY>
AI_MOCK_MODE=1
EOF

# systemd 등록
sudo cp systemd/ai-inference.service /etc/systemd/system/ai-inference.service
sudo systemctl daemon-reload
sudo systemctl enable ai-inference
sudo systemctl start ai-inference
sudo systemctl status ai-inference
```

### 9.4 AI 사설 IP → Secret 등록
```bash
AI_INTERNAL_IP="$(gcloud compute instances describe "${AI_VM}" --zone "${ZONE}" --format='value(networkInterfaces[0].networkIP)')"
echo "AI_INTERNAL_IP=${AI_INTERNAL_IP}"

echo -n "http://${AI_INTERNAL_IP}:${AI_PORT}" | gcloud secrets create BAKE_SIGHT_AI_BASE_URL --data-file=-
```

---

## 10) Central API(Cloud Run) 배포
### 10.1 이미지 빌드
```bash
cd central-api
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/central-api:latest"
gcloud builds submit --tag "${IMAGE}"
```

### 10.2 배포(Direct VPC egress + Cloud SQL + Secrets)
```bash
gcloud run deploy "${CENTRAL_SERVICE}"   --image "${IMAGE}"   --region "${REGION}"   --service-account "${CENTRAL_SA}"   --network "${VPC}"   --subnet "${SUBNET}"   --network-tags "${CENTRAL_NET_TAG}"   --vpc-egress "private-ranges-only"   --add-cloudsql-instances "${INSTANCE_CONNECTION_NAME}"   --update-secrets     "ADMIN_KEY=BAKE_SIGHT_ADMIN_KEY:latest,DATABASE_URL=BAKE_SIGHT_DATABASE_URL:latest,AI_ADMIN_KEY=BAKE_SIGHT_AI_ADMIN_KEY:latest,AI_BASE_URL=BAKE_SIGHT_AI_BASE_URL:latest"   --update-env-vars "CREATE_TABLES=1"   --allow-unauthenticated
```

테이블 생성 확인 후:
```bash
gcloud run services update "${CENTRAL_SERVICE}"   --region "${REGION}"   --update-env-vars "CREATE_TABLES=0"
```

---

## 11) 검증
Cloud Run URL:
```bash
CENTRAL_URL="$(gcloud run services describe "${CENTRAL_SERVICE}" --region "${REGION}" --format='value(status.url)')"
echo "${CENTRAL_URL}"
```

API 호출 테스트:
```bash
curl -H "X-ADMIN-KEY: <CENTRAL_ADMIN_KEY>" "${CENTRAL_URL}/api/v1/stores"
```

Tray 추론 E2E:
- tray_session 생성 후
- Central이 AI VM을 호출하고 `recognition_run` 저장 + (REVIEW/UNKNOWN이면) `review` 자동 생성

```bash
curl -X POST   -H "X-ADMIN-KEY: <CENTRAL_ADMIN_KEY>"   -H "Content-Type: application/json"   "${CENTRAL_URL}/api/v1/tray-sessions/<SESSION_UUID>/infer"   -d '{"frames_b64":["<BASE64_1>","<BASE64_2>"]}'
```

---

## 12) 운영 팁(2주 데모)
- AI VM은 미사용 시 `gcloud compute instances stop`으로 비용 절감
- GCS는 lifecycle rule로 14일 후 자동 삭제 권장
- AI 장애 시 Central은 수동 리뷰(결제 보호)로 fallback 운영 권장

---

## 부록: Serverless VPC Connector로 붙이는 대안(필요 시)
조직 정책/환경에 따라 Direct VPC egress 대신 Serverless VPC Access Connector를 쓰는 구성도 가능합니다.
이 경우에는 커넥터 생성 후 Cloud Run에 `--vpc-connector`를 지정합니다.
