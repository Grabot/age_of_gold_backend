"""Test util mail send reset password mail."""

from unittest.mock import MagicMock, patch

from sib_api_v3_sdk import SendSmtpEmail

from src.config.config import settings
from src.util.mail.reset_password_mail import load_email_template, send_reset_email


def test_load_email_template_success() -> None:
    """Test that the email template is loaded and placeholders are replaced."""
    mock_template = "<html>{frontend_url}{access_token}{year}</html>"
    access_token = "test_token"

    with patch("pathlib.Path.read_text", return_value=mock_template):
        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.now.return_value.year = 2000
            result = load_email_template(access_token)

    assert settings.FRONTEND_URL in result
    assert access_token in result
    assert "2000" in result


def test_send_reset_email_success() -> None:
    """Test that send_reset_email prepares the email correctly and calls the Brevo API."""
    mock_template = "<html>{frontend_url}{access_token}{year}</html>"
    to_email = "test@example.com"
    subject = "Reset your password"
    access_token = "test_token"

    with patch("src.util.mail.reset_password_mail.api_instance") as mock_api_instance:
        with patch("pathlib.Path.read_text", return_value=mock_template):
            mock_send_transac_email = MagicMock()
            mock_api_instance.send_transac_email = mock_send_transac_email

            send_reset_email(to_email, subject, access_token)

            mock_send_transac_email.assert_called_once()
            call_args = mock_send_transac_email.call_args
            assert call_args is not None
            email_body = call_args[0][0]

            assert isinstance(email_body, SendSmtpEmail)
            assert email_body.subject == subject
