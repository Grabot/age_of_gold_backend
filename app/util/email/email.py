import asyncio
import multiprocessing
from typing import List

from config import settings
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr


class EmailSchema(BaseModel):
    email: List[EmailStr]


conf = ConnectionConfig(
    MAIL_USERNAME="Age of Gold",
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_USERNAME,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


class EmailProcess(multiprocessing.Process):
    def __init__(self, email_address, email_subject, html_body):
        super(EmailProcess, self).__init__()
        self.email = email_address
        self.email_subject = email_subject
        self.html_body = html_body

    def run(self):
        print("sending email: %s" % self.email)
        recipients = [self.email]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_email(self.email_subject, recipients, self.html_body))
        print("done sending")


async def send_email(subject, recipients, html_body):
    message = MessageSchema(
        subject=subject, recipients=recipients, body=html_body, subtype=MessageType.html
    )
    fm = FastMail(conf)
    await fm.send_message(message)
