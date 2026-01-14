from __future__ import annotations

import os
from datetime import timedelta
from google.cloud import storage

from app.core.config import settings

def _get_storage_client() -> storage.Client:
    """서비스 계정 키가 있으면 사용, 없으면 기본 자격증명"""
    key_path = settings.GOOGLE_APPLICATION_CREDENTIALS
    if key_path and os.path.exists(key_path):
        return storage.Client.from_service_account_json(key_path)
    return storage.Client()

def upload_bytes(bucket_name: str, object_name: str, data: bytes, content_type: str) -> str:
    """바이트 데이터를 GCS에 업로드하고 gs:// URI 반환"""
    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(data, content_type=content_type)
    return f"gs://{bucket_name}/{object_name}"


def generate_signed_url(gcs_uri: str, expiration_minutes: int = 60) -> str:
    """GCS 객체에 대한 서명된 URL 생성"""
    if not gcs_uri.startswith("gs://"):
        raise ValueError("잘못된 GCS URI 형식")

    # gs://bucket-name/object-path 파싱
    path = gcs_uri[5:]  # "gs://" 제거
    parts = path.split("/", 1)
    if len(parts) != 2:
        raise ValueError("잘못된 GCS URI 형식")

    bucket_name, object_name = parts

    try:
        client = _get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(object_name)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )
        return url
    except Exception as e:
        # 개발 환경용 공개 URL 폴백 (버킷이 공개 설정이어야 함)
        print(f"[WARN] 서명된 URL 생성 실패, 공개 URL로 폴백: {e}")
        return f"https://storage.googleapis.com/{bucket_name}/{object_name}"
