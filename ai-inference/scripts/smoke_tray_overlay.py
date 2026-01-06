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

from dotenv import load_dotenv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # ai-inference 루트
load_dotenv(os.path.join(ROOT, ".env"), override=True)

import app.services.engine as eng_mod
print("engine.py =", eng_mod.__file__)
print("env now   =", os.getenv("KNN_TOPK"), os.getenv("UNKNOWN_DIST_TH"), os.getenv("MARGIN_TH"))

from app.services.engine import InferenceEngine
eng = InferenceEngine()
print("engine val=", eng.knn_topk, eng.unknown_dist_th, eng.margin_th)

def img_to_b64(path: str) -> str:
    raw = Path(path).read_bytes()
    return base64.b64encode(raw).decode("utf-8")


def fetch_name_eng_map(item_ids: list[int]) -> dict[int, str]:
    """menu 테이블에서 item_id -> name_eng 매핑 조회"""
    if not item_ids:
        return {}

    host = os.environ.get("DB_HOST", "127.0.0.1")
    port = int(os.environ.get("DB_PORT", "3307"))
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

    w, h = img.size
    font_size = max(20, int(min(w, h) * 0.015))
    font_path = os.environ.get("FONT_PATH", "").strip()

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
        font = ImageFont.load_default()

    for inst in instances:
        bbox = inst.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        x1, y1, x2, y2 = [int(v) for v in bbox]
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        state = (inst.get("state") or "").upper()

        if state == "UNKNOWN":
            bd = inst.get("best_dist", None)
            text = "UNKNOWN" if bd is None else f"UNKNOWN({float(bd):.3f})"
        else:
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

    print("YOLO loaded:", eng.yolo is not None)
    print("YOLO params:", eng.yolo_imgsz, eng.yolo_conf, eng.yolo_iou, eng.ai_device)
    print("KNN params:", eng.knn_topk, eng.unknown_dist_th, eng.margin_th)
    print("has _resolve_yolo_local_path:", hasattr(eng, "_resolve_yolo_local_path"))
    print("YOLO_MODEL_URI (os.getenv):", os.getenv("YOLO_MODEL_URI"))

    # 2) 테스트 이미지 폴더 경로 (본인 환경에 맞게 수정)
    input_dir = "/home/ram/Downloads/TEST"
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"input dir not found: {input_dir}")

    # output 폴더: 인풋 폴더명에 _output 붙이기
    output_dir = input_dir.rstrip("/\\") + "_output"
    os.makedirs(output_dir, exist_ok=True)

    exts = {".png", ".jpg", ".jpeg"}
    img_paths = []

    for root, dirs, files in os.walk(input_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in exts:
                img_paths.append(os.path.join(root, f))

    img_paths.sort()
    if not img_paths:
        raise FileNotFoundError(f"no images found in: {input_dir}")

    for idx, img_path in enumerate(img_paths, 1):
        print(f"\n[{idx}/{len(img_paths)}] {img_path}")

        payload = {
            "session_uuid": str(uuid.uuid4()),
            "attempt_no": 1,
            "store_code": "TEST_STORE",
            "device_code": "TEST_DEVICE",
            "frame_b64": img_to_b64(img_path),
        }

        try:
            res = eng.infer_tray(payload)
        except Exception as e:
            print("infer error:", e)
            continue

        # print(json.dumps(res, ensure_ascii=False, indent=2))
        print(json.dumps(res, ensure_ascii=False, separators=(",", ":")))

        # 3) item_id들 모아서 DB에서 name_eng 조회
        instances = res.get("result_json", {}).get("instances", [])
        item_ids = []
        for inst in instances:
            if inst.get("state") == "UNKNOWN":
                continue
            item_ids.append(int(inst.get("best_item_id")))

        item_ids = sorted(set(item_ids))

        try:
            id2name = fetch_name_eng_map(item_ids)
        except Exception as e:
            print("db error:", e)
            id2name = {}

        # 4) 오버레이 이미지 생성
        frame_path = res.get("result_json", {}).get("local_frame_path", "")
        if not frame_path or not os.path.exists(frame_path):
            print("local_frame_path not found:", frame_path)
            continue

        # overlay_result.jpg가 frame_path 폴더에 생성됨
        tmp_out_path = draw_overlay(frame_path, instances, id2name)

        # ✅ input 폴더의 상대 경로를 유지해서 output에도 동일하게 생성
        rel_path = os.path.relpath(img_path, input_dir)           # 예: sub/a.jpg
        rel_dir = os.path.dirname(rel_path)                       # 예: sub
        save_dir = os.path.join(output_dir, rel_dir)              # 예: .../test_images_output/sub
        os.makedirs(save_dir, exist_ok=True)

        # ✅ 제가 정한 파일명 규칙: 0001_stem_overlay.jpg
        stem = Path(img_path).stem
        final_name = f"{idx:04d}_{stem}_overlay.jpg"
        final_out_path = os.path.join(save_dir, final_name)

        try:
            os.replace(tmp_out_path, final_out_path)  # move (덮어쓰기 포함)
            print("overlay saved:", final_out_path)
        except Exception as e:
            print("move error:", e)
            print("overlay saved (tmp):", tmp_out_path)
