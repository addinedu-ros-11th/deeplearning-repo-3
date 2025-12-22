# GCP 배포 가이드 (Cloud Run + Cloud SQL MySQL)

본 프로젝트를 **Cloud Run + Cloud SQL(MySQL)**로 배포하는 권장 절차를 정리합니다.
데모 프로젝트 기준으로 **실수 가능성을 줄이기 위해 “전용 서비스 계정”을 만들어 배포**하는 흐름을 기본으로 합니다.

## 핵심 개념
- Cloud Run에서 Cloud SQL을 연결하면, 런타임 파일시스템에 소켓 경로 `/cloudsql/<INSTANCE_CONNECTION_NAME>`가 제공됩니다.
- `INSTANCE_CONNECTION_NAME` 형식: `project:region:instance-id`
- 본 프로젝트는 SQLAlchemy + PyMySQL을 사용하며 **Unix 소켓 방식** 연결을 권장합니다.

---

## 1) 선행 준비(1회)

### 1.1 gcloud 로그인 및 프로젝트 설정
```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
```

### 1.2 필요한 API 활성화
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com
```

### 1.3 Artifact Registry 리포지토리 생성(1회)
```bash
gcloud artifacts repositories create <REPO_NAME> \
  --repository-format=docker \
  --location <REGION> \
  --description "Smart Cafe Demo images"
```

---

## 2) Cloud SQL(MySQL) 설정(요약)
1) Cloud SQL for MySQL 인스턴스 생성
2) DB 생성(예: `smart_cafe_demo`)
3) DB 유저/비밀번호 생성

---

## 3) 전용 서비스 계정 생성 및 권한 부여(권장)

Cloud Run이 **Cloud SQL**과 **Secret Manager**에 접근할 수 있어야 하므로, 서비스 계정에 권한을 부여합니다.

### 3.1 서비스 계정 생성(1회)
```bash
gcloud iam service-accounts create smart-cafe-run \
  --display-name "Smart Cafe Cloud Run"
```

서비스 계정 이메일(자동 생성)을 아래처럼 사용합니다:
```bash
SA_EMAIL="smart-cafe-run@<PROJECT_ID>.iam.gserviceaccount.com"
```

### 3.2 Cloud SQL Client 권한 부여(프로젝트 단위)
```bash
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client"
```

### 3.3 Secret Manager 접근 권한 부여(Secret 단위 권장)
Secret 자체는 아래 4)에서 생성합니다. 생성 후 다음을 실행하세요:
```bash
gcloud secrets add-iam-policy-binding SMART_CAFE_ADMIN_KEY \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding SMART_CAFE_DATABASE_URL \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"
```

---

## 4) Secret Manager에 민감정보 저장(권장)

### 4.1 Admin Key 저장(최초 1회)
```bash
echo -n "<ADMIN_KEY_VALUE>" | gcloud secrets create SMART_CAFE_ADMIN_KEY --data-file=-
```

이미 secret이 존재하면 “버전 추가”로 갱신합니다:
```bash
echo -n "<ADMIN_KEY_VALUE>" | gcloud secrets versions add SMART_CAFE_ADMIN_KEY --data-file=-
```

### 4.2 DATABASE_URL 저장(최초 1회)
Cloud Run + Cloud SQL(Unix socket) 예시:
```text
mysql+pymysql://DBUSER:DBPASS@/DBNAME?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE&charset=utf8mb4
```

생성:
```bash
echo -n "mysql+pymysql://DBUSER:DBPASS@/DBNAME?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE&charset=utf8mb4" \
 | gcloud secrets create SMART_CAFE_DATABASE_URL --data-file=-
```

이미 secret이 존재하면 버전 추가:
```bash
echo -n "mysql+pymysql://DBUSER:DBPASS@/DBNAME?unix_socket=/cloudsql/PROJECT:REGION:INSTANCE&charset=utf8mb4" \
 | gcloud secrets versions add SMART_CAFE_DATABASE_URL --data-file=-
```

---

## 5) 컨테이너 빌드 및 푸시

### 5.1 Cloud Build로 빌드/푸시(가장 단순)
```bash
gcloud builds submit \
  --tag <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/smart-cafe-api:latest
```

---

## 6) Cloud Run 배포

### 6.1 Cloud Run 배포 + Cloud SQL 연결 + Secret 주입
```bash
SA_EMAIL="smart-cafe-run@<PROJECT_ID>.iam.gserviceaccount.com"

gcloud run deploy smart-cafe-api \
  --image <REGION>-docker.pkg.dev/<PROJECT_ID>/<REPO_NAME>/smart-cafe-api:latest \
  --region <REGION> \
  --service-account "${SA_EMAIL}" \
  --add-cloudsql-instances <PROJECT:REGION:INSTANCE> \
  --update-secrets ADMIN_KEY=SMART_CAFE_ADMIN_KEY:latest,DATABASE_URL=SMART_CAFE_DATABASE_URL:latest \
  --update-env-vars CREATE_TABLES=1,DB_POOL_SIZE=5,DB_MAX_OVERFLOW=2,DB_POOL_RECYCLE=1800 \
  --allow-unauthenticated
```

### 6.2 테이블 생성 후 CREATE_TABLES 끄기
```bash
gcloud run services update smart-cafe-api \
  --region <REGION> \
  --update-env-vars CREATE_TABLES=0
```

---

## 7) 배포 후 확인

### 7.1 서비스 URL 확인
```bash
gcloud run services describe smart-cafe-api --region <REGION> --format='value(status.url)'
```

### 7.2 /docs 접속
- `https://<SERVICE_URL>/docs`

### 7.3 API 호출 예시
```bash
curl -H "X-ADMIN-KEY: <ADMIN_KEY_VALUE>" \
  "https://<SERVICE_URL>/api/v1/stores"
```

---

## 8) 체크리스트(실수 방지)
- [ ] Cloud Run 서비스에 Cloud SQL 인스턴스 연결(`--add-cloudsql-instances`) 누락 여부
- [ ] DATABASE_URL의 `unix_socket=/cloudsql/...` 경로 및 인스턴스 이름 오타 여부
- [ ] Cloud Run 서비스 계정이 `roles/cloudsql.client`를 가지고 있는지
- [ ] 서비스 계정이 Secret에 대해 `roles/secretmanager.secretAccessor`를 가지고 있는지
- [ ] 최초 배포 이후 `CREATE_TABLES=0`으로 되돌렸는지
