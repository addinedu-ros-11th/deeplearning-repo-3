from __future__ import annotations
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
