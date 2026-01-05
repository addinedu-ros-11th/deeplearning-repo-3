import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import base64
import json
import uuid
from pathlib import Path

from app.services.engine import InferenceEngine  # 경로가 다르면 맞춰주세요


def img_to_b64(path: str) -> str:
    raw = Path(path).read_bytes()
    return base64.b64encode(raw).decode("utf-8")


if __name__ == "__main__":
    eng = InferenceEngine()
    eng.startup_load()

    payload = {
        "session_uuid": str(uuid.uuid4()),
        "attempt_no": 1,
        "store_code": "TEST_STORE",
        "device_code": "TEST_DEVICE",
        "frame_b64": img_to_b64("/home/ram/Downloads/test1.png"),  # 테스트 이미지 경로로 변경
    }

    res = eng.infer_tray(payload)
    print(json.dumps(res, ensure_ascii=False, indent=2))
