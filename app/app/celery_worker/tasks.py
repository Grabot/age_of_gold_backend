import requests
from celery import Celery
from sqlalchemy.orm import Session
from sqlmodel import select

from app import database
from app.config.config import settings
from app.models import UserToken
from app.util.avatar.generate_avatar import generate_avatar
from app.util.email.send_email import send_email

celery_app = Celery("tasks", broker=settings.REDIS_URI, backend=f"db+{settings.SYNC_DB_URL}")


@celery_app.task
def task_generate_avatar(avatar_filename: str, user_id: int):
    print("going to generate avatar")
    generate_avatar(avatar_filename, settings.UPLOAD_FOLDER_AVATARS)

    base_url = settings.BASE_URL
    api_prefix = settings.API_V1_STR
    endpoint = "/avatar/created"
    total_url = base_url + api_prefix + endpoint
    print(f"url {total_url}")
    get_result = requests.post(total_url, json={"user_id": user_id})
    print(f"getting result {get_result}")

    return {"success": True}


@celery_app.task
def task_send_email(username: str, recipients: str, subject: str, body: str):
    send_email(
        settings.MAIL_SENDERNAME,
        settings.MAIL_USERNAME,
        settings.MAIL_PASSWORD,
        username,
        recipients,
        subject,
        body,
    )

    return {"success": True}


@celery_app.task
def task_remove_expired_tokens():
    with Session(database.engine_sync) as session:
        statement = select(UserToken)
        results = session.execute(statement)
        result = results.all()

        for token in result:
            user_token: UserToken = token.UserToken
            if user_token.refresh_is_expired():
                session.delete(user_token)
        session.commit()

    return {"success": True}
