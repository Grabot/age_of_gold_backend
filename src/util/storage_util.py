from io import BytesIO
from typing import Any
from cryptography.fernet import Fernet


def download_image(
    s3_client: Any, cipher: Fernet, bucket: str, key: str, encrypted: bool = True
) -> bytes:
    """Download an image from S3."""
    buffer = BytesIO()
    s3_client.download_fileobj(bucket, key, buffer)
    buffer.seek(0)

    if encrypted:
        return decrypt_image(buffer.getvalue(), cipher)
    else:
        # Default avatars are not encrypted
        return buffer.read()


def upload_image(
    s3_client: Any, cipher: Fernet, avatar_bytes: bytes, bucket: str, s3_key: str
) -> None:
    """Upload an image to S3."""
    buffer = BytesIO()
    encrypted_data = cipher.encrypt(avatar_bytes)
    buffer.write(encrypted_data)
    content_type = "application/octet-stream"

    buffer.seek(0)
    s3_client.upload_fileobj(
        buffer, bucket, s3_key, ExtraArgs={"ContentType": content_type}
    )


def decrypt_image(encrypted_data: bytes, cipher: Fernet) -> bytes:
    """Decrypt an image."""
    return cipher.decrypt(encrypted_data)
