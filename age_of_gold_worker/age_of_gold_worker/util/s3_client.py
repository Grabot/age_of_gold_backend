import boto3
from botocore.client import Config
from typing import Any, Optional
from age_of_gold_worker.age_of_gold_worker.worker_settings import worker_settings

_s3_client: Optional[Any] = None


def get_s3_client() -> Any:
    """Get a singleton S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=worker_settings.S3_ENDPOINT,
            aws_access_key_id=worker_settings.S3_ACCESS_KEY,
            aws_secret_access_key=worker_settings.S3_SECRET_KEY,
            region_name="eu-central-1",
            config=Config(signature_version="s3v4"),
        )
    return _s3_client
