from __future__ import annotations
import os
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from google.cloud import storage

def parse_gs_uri(gs_uri: str) -> tuple[str, str]:
    u = urlparse(gs_uri)
    if u.scheme != "gs":
        raise ValueError("not gs:// uri")
    return u.netloc, u.path.lstrip("/")

def download_to(gs_uri: str, dest_path: str) -> str:
    bucket_name, blob_name = parse_gs_uri(gs_uri)
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    p = Path(dest_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(str(p))
    return str(p)

def load_latest_model(bucket_name, prefix, model_key):
    """
    GCS에서 prefix + model_key 로 시작하는 pkl 중
    가장 최신 파일을 다운로드 후 로컬 경로 반환
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    blobs = list(bucket.list_blobs(prefix=prefix))
    candidates = [
        b for b in blobs
        if model_key in b.name and b.name.endswith(".pkl")
    ]

    if not candidates:
        raise FileNotFoundError(
            f"No model found for key={model_key} in GCS"
        )

    # 파일명 기준 최신 정렬
    candidates.sort(key=lambda x: x.name, reverse=True)
    latest_blob = candidates[0]

    # 임시 파일로 다운로드
    tmp_dir = tempfile.gettempdir()
    local_path = os.path.join(tmp_dir, os.path.basename(latest_blob.name))
    latest_blob.download_to_filename(local_path)

    return local_path