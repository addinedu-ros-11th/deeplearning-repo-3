# AI Inference (Compute Engine GPU VM)
- FastAPI 기반 추론 API
- 기본(Mock) 모드: `AI_MOCK_MODE=1`
- 보안: `X-AI-KEY` 헤더 필수

## 빠른 실행(Mock)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export AI_ADMIN_KEY=CHANGE_ME
export AI_MOCK_MODE=1
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

## systemd
- `/etc/ai-inference.env`에 환경변수 저장
- `systemd/ai-inference.service` 등록 후 enable/start
