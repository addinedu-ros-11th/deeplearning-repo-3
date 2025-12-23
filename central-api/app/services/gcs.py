from __future__ import annotations

from google.cloud import storage

def upload_bytes(bucket_name: str, object_name: str, data: bytes, content_type: str) -> str:
    """Upload bytes to GCS and return gs:// URI."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)
    blob.upload_from_string(data, content_type=content_type)
    return f"gs://{bucket_name}/{object_name}"
