from __future__ import annotations
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from google.cloud import storage
import joblib

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


def upload_to_gcs(local_path: str, bucket_name: str, blob_name: str) -> str:
    """로컬 파일을 GCS 버킷에 업로드"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{blob_name}"


def load_latest_model(bucket_name: str, prefix: str, model_type: str, local_dir: str | None = None):
    """
    GCS 버킷에서 최신 모델 파일을 다운로드하고 로드

    Args:
        bucket_name: GCS 버킷 이름
        prefix: 모델 파일 prefix (예: "cctv_fall_down_")
        model_type: 모델 파일 확장자 또는 타입 (예: ".pt", ".joblib")
        local_dir: .pt 파일 저장 디렉토리 (None이면 tempdir 사용)

    Returns:
        .pt 파일: 로컬 경로 (str)
        .joblib 파일: 로드된 모델 객체
    """
    import os
    import logging

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))

    # model_type을 포함하는 파일만 필터링
    matching_blobs = [b for b in blobs if model_type in b.name]

    if not matching_blobs:
        raise FileNotFoundError(f"No model found for {prefix}*{model_type}* in {bucket_name}")

    # 가장 최근에 업데이트된 파일 선택
    latest_blob = max(matching_blobs, key=lambda b: b.updated)
    blob_filename = latest_blob.name.split('/')[-1]

    logging.info(f"Latest model found: gs://{bucket_name}/{latest_blob.name}")

    # .pt 파일: 로컬 경로 반환
    if blob_filename.endswith('.pt'):
        if local_dir is None:
            local_dir = os.path.join(tempfile.gettempdir(), "yolo_models")
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        local_path = str(Path(local_dir) / blob_filename)

        if not os.path.exists(local_path):
            logging.info(f"Downloading model to: {local_path}")
            latest_blob.download_to_filename(local_path)
        else:
            logging.info(f"Model already cached: {local_path}")

        return local_path

    # .joblib 파일: 모델 객체 반환
    with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp:
        latest_blob.download_to_filename(tmp.name)
        model = joblib.load(tmp.name)

    return model


def upload_to_gcs(local_path: str, bucket_name: str, blob_name: str) -> str:
    """로컬 파일을 GCS 버킷에 업로드"""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    return f"gs://{bucket_name}/{blob_name}"


def load_latest_model(bucket_name: str, prefix: str, model_type: str, local_dir: str | None = None):
    """GCS 버킷에서 최신 모델 파일을 다운로드하고 로드"""
    import os
    import logging

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))

    # model_type을 포함하는 파일만 필터링
    matching_blobs = [b for b in blobs if model_type in b.name]

    if not matching_blobs:
        raise FileNotFoundError(f"No model found for {prefix}*{model_type}* in {bucket_name}")

    # 가장 최근에 업데이트된 파일 선택
    latest_blob = max(matching_blobs, key=lambda b: b.updated)
    blob_filename = latest_blob.name.split('/')[-1]

    logging.info(f"Latest model found: gs://{bucket_name}/{latest_blob.name}")

    # .pt 파일: 로컬 경로 반환
    if blob_filename.endswith('.pt'):
        if local_dir is None:
            local_dir = os.path.join(tempfile.gettempdir(), "yolo_models")
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        local_path = str(Path(local_dir) / blob_filename)

        if not os.path.exists(local_path):
            logging.info(f"Downloading model to: {local_path}")
            latest_blob.download_to_filename(local_path)
        else:
            logging.info(f"Model already cached: {local_path}")

        return local_path

    # .joblib 파일: 모델 객체 반환
    with tempfile.NamedTemporaryFile(delete=False, suffix='.joblib') as tmp:
        latest_blob.download_to_filename(tmp.name)
        model = joblib.load(tmp.name)

    return model