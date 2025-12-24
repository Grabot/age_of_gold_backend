from io import BytesIO
from age_of_gold_worker.age_of_gold_worker.util import s3_client


def worker_upload_image(avatar_bytes: bytes, bucket: str, s3_key: str) -> None:
    """Upload an image to S3 (with optional encryption)."""
    s3 = s3_client.get_s3_client()
    buffer = BytesIO()
    buffer.write(avatar_bytes)
    buffer.seek(0)
    content_type = "image/png"
    s3.upload_fileobj(buffer, bucket, s3_key, ExtraArgs={"ContentType": content_type})
