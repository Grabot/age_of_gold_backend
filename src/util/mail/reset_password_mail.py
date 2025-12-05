import datetime
from pathlib import Path

from sib_api_v3_sdk import (
    ApiClient,
    Configuration,
    SendSmtpEmail,
    SendSmtpEmailSender,
    SendSmtpEmailTo,
    TransactionalEmailsApi,
)

from src.config.config import settings

configuration = Configuration()
configuration.api_key["api-key"] = settings.MAIL_API_KEY
api_instance = TransactionalEmailsApi(ApiClient(configuration))


def load_email_template(access_token: str) -> str:
    """Load the email template."""
    template_path = Path("src/templates/password_reset_template.html")
    template = template_path.read_text()
    current_year = datetime.datetime.now().year
    return (
        template.replace("{frontend_url}", settings.FRONTEND_URL)
        .replace("{access_token}", access_token)
        .replace("{year}", str(current_year))
    )


def send_reset_email(to_email: str, subject: str, access_token: str) -> None:
    """Send reset email to user."""
    to = SendSmtpEmailTo(email=to_email)
    sender = SendSmtpEmailSender(name=settings.SENDER_NAME, email=settings.SENDER_MAIL)
    html_content = load_email_template(
        access_token,
    )
    email_body = SendSmtpEmail(
        to=[to],
        sender=sender,
        subject=subject,
        html_content=html_content,
    )
    api_instance.send_transac_email(email_body)
