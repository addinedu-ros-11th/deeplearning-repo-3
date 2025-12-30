import os
import sys
import json
import uuid
import base64
from pathlib import Path

import pymysql
from PIL import Image, ImageDraw, ImageFont

# app import가 되도록 ai-inference 루트를 sys.path에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.engine import InferenceEngine

from dotenv import load_dotenv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # ai-inference 루트
load_dotenv(os.path.join(ROOT, ".env"))


def img_to_b64(path: str) -> str:
    raw = Path(path).read_bytes()
    return base64.b64encode(raw).decode("utf-8")


def fetch_name_eng_map(item_ids: list[int]) -> dict[int, str]:
    """menu 테이블에서 item_id -> name_eng 매핑 조회"""
    if not item_ids:
        return {}

    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "3306"))
    user = os.environ.get("DB_USER", "root")
    pw = os.environ.get("DB_PASSWORD", "")
    db = os.environ.get("DB_NAME", "")

    if not db:
        raise RuntimeError("DB_NAME is empty. .env에 DB_NAME을 설정하세요.")

    placeholders = ",".join(["%s"] * len(item_ids))
    sql = f"""
        SELECT item_id, name_eng
        FROM menu_item
        WHERE item_id IN ({placeholders})
    """

    conn = pymysql.connect(
        host=host, port=port, user=user, password=pw, database=db,
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, item_ids)
            rows = cur.fetchall()
        return {int(r["item_id"]): (r["name_eng"] or "") for r in rows}
    finally:
        conn.close()

def draw_overlay(frame_path: str, instances: list[dict], id2name: dict[int, str]) -> str:
    img = Image.open(frame_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ✅ 영문 폰트 경로: .env의 FONT_PATH 사용
    # font_size = 50
    w, h = img.size
    font_size = max(20, int(min(w, h) * 0.03))
    font_path = os.environ.get("FONT_PATH", "").strip()

    # fallback 후보(리눅스에 흔함)
    candidates = [
        font_path,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    font = None
    for p in candidates:
        if p and os.path.exists(p):
            try:
                font = ImageFont.truetype(p, font_size)
                break
            except Exception:
                font = None

    if font is None:
        # 최후 fallback: 크기 조절 불가(작게 나오는 게 정상)
        font = ImageFont.load_default()

    for inst in instances:
        if inst.get("state") == "UNKNOWN":
            continue

        bbox = inst.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        x1, y1, x2, y2 = [int(v) for v in bbox]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        item_id = int(inst.get("best_item_id", -1))
        text = id2name.get(item_id, f"item-{item_id}")

        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        tw = r - l
        th = b - t

        tx = cx - (tw // 2)
        ty = cy - (th // 2)

        pad = 6
        draw.rectangle([tx - pad, ty - pad, tx + tw + pad, ty + th + pad], fill=(0, 0, 0))
        draw.text((tx, ty), text, fill=(255, 255, 255), font=font)

    out_path = str(Path(frame_path).with_name("overlay_result.jpg"))
    img.save(out_path, quality=95)
    return out_path


if __name__ == "__main__":
    # 1) 엔진 실행
    eng = InferenceEngine()
    eng.startup_load()

    # 2) 테스트 이미지 경로 (본인 환경에 맞게 수정)
    test_img_path = "/home/ram/Downloads/test3.png"
    if not os.path.exists(test_img_path):
        raise FileNotFoundError(f"test image not found: {test_img_path}")

    payload = {
        "session_uuid": str(uuid.uuid4()),
        "attempt_no": 1,
        "store_code": "TEST_STORE",
        "device_code": "TEST_DEVICE",
        "frame_b64": img_to_b64(test_img_path),
    }

    res = eng.infer_tray(payload)
    print(json.dumps(res, ensure_ascii=False, indent=2))

    # 3) item_id들 모아서 DB에서 name_eng 조회
    instances = res.get("result_json", {}).get("instances", [])
    item_ids = []
    for inst in instances:
        if inst.get("state") == "UNKNOWN":
            continue
        item_ids.append(int(inst.get("best_item_id")))

    item_ids = sorted(set(item_ids))
    id2name = fetch_name_eng_map(item_ids)

    # 4) 오버레이 이미지 생성
    frame_path = res.get("result_json", {}).get("local_frame_path", "")
    if not frame_path or not os.path.exists(frame_path):
        raise FileNotFoundError(f"local_frame_path not found: {frame_path}")

    out_path = draw_overlay(frame_path, instances, id2name)
    print("overlay saved:", out_path)
