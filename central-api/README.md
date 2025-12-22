# Central API (Cloud Run)

- FastAPI + SQLAlchemy(MySQL)
- Cloud Run 배포를 기본 목표로 구성
- Admin Key 기반 단일 인증(`X-ADMIN-KEY`)
- Tray/CCTV 이벤트 저장, 리뷰 처리, 주문/대시보드 API 제공
- (옵션) AI Inference 서버(Compute Engine GPU VM)로 추론 요청
  - `POST /api/v1/tray-sessions/{session_uuid}/infer`

## 로컬 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

모든 API는 헤더 `X-ADMIN-KEY: <ADMIN_KEY>` 필요
