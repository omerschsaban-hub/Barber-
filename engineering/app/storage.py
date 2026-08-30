from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse


class StorageConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class ObjectRef:
    key: str
    size_bytes: int
    sha256: str
    content_type: str
    download_url: str | None


def _settings() -> tuple[str, str, str, str, str]:
    bucket = os.getenv("STORAGE_BUCKET", "").strip()
    endpoint = os.getenv("STORAGE_ENDPOINT", "").strip()
    access_key = os.getenv("STORAGE_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("STORAGE_SECRET_ACCESS_KEY", "").strip()
    region = os.getenv("STORAGE_REGION", "us-east-1").strip() or "us-east-1"
    return bucket, endpoint, access_key, secret_key, region


def configured() -> bool:
    bucket, endpoint, access_key, secret_key, _ = _settings()
    return bool(bucket and endpoint and access_key and secret_key)


def _client():
    bucket, endpoint, access_key, secret_key, region = _settings()
    if not all((bucket, endpoint, access_key, secret_key)):
        raise StorageConfigurationError(
            "Durable object storage is not configured. Set STORAGE_BUCKET, STORAGE_ENDPOINT, "
            "STORAGE_ACCESS_KEY_ID and STORAGE_SECRET_ACCESS_KEY."
        )
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" and os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise StorageConfigurationError("Production object storage endpoint must use HTTPS.")
    try:
        import boto3
    except ImportError as exc:
        raise StorageConfigurationError("boto3 is required for durable object storage.") from exc
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    ), bucket


def put_bytes(*, prefix: str, data: bytes, content_type: str, sha256: str) -> ObjectRef:
    client, bucket = _client()
    safe_prefix = "/".join(part for part in prefix.strip("/").split("/") if part and part not in {".", ".."})
    key = f"{safe_prefix}/{uuid.uuid4().hex}" if safe_prefix else uuid.uuid4().hex
    client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type, Metadata={"sha256": sha256})
    expires = max(60, min(int(os.getenv("STORAGE_SIGNED_URL_TTL", "900")), 86400))
    url = client.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires)
    return ObjectRef(key=key, size_bytes=len(data), sha256=sha256, content_type=content_type, download_url=url)


def require_durable_storage() -> None:
    if os.getenv("ENVIRONMENT", "development").lower() == "production" and not configured():
        raise StorageConfigurationError("Durable object storage is required in production; refusing ephemeral-only artifacts.")
