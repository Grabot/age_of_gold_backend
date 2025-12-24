"""Endpoint for getting user avatar."""

from typing import Tuple, Any
from io import BytesIO

from fastapi import Depends, HTTPException, Security, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from botocore.exceptions import ClientError

from src.api.api_v1.router import api_router_v1
from src.config.config import settings
from src.database import get_db
from src.models.user import User
from src.models.user_token import UserToken
from src.util.decorators import handle_db_errors
from src.util.gold_logging import logger
from src.util.security import checked_auth_token
from src.util.storage_util import download_image


@api_router_v1.get("/user/avatar", status_code=200)
@handle_db_errors("Get avatar failed")
async def get_avatar(
    request: Request,
    get_default: bool = False,
    user_and_token: Tuple[User, UserToken] = Security(
        checked_auth_token, scopes=["user"]
    ),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Handle get avatar request."""
    user, _ = user_and_token
    s3_client: Any = request.app.state.s3
    cipher: Any = request.app.state.cipher

    encrypted = not (user.default_avatar or get_default)
    file_name = (
        user.avatar_filename_default()
        if (user.default_avatar or get_default)
        else user.avatar_filename()
    )
    s3_key: str = user.avatar_s3_key(file_name)
    try:
        decrypted_data: bytes = download_image(
            s3_client, cipher, settings.S3_BUCKET_NAME, s3_key, encrypted
        )
        decrypted_buffer: BytesIO = BytesIO(decrypted_data)
        decrypted_buffer.seek(0)
        return StreamingResponse(
            decrypted_buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename={file_name}"},
        )
    except ClientError as e:
        logger.error("Failed to fetch avatar: %s", str(e))
        if e.response["Error"]["Code"] == "NoSuchKey":
            raise HTTPException(status_code=404, detail="Avatar not found") from e
        raise HTTPException(status_code=500, detail="Failed to fetch avatar") from e
