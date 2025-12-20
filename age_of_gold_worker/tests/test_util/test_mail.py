"""Test for mail utilities."""

import datetime
from unittest.mock import patch, MagicMock
import pytest
from pytest_mock import MockerFixture
from age_of_gold_worker.age_of_gold_worker.util.mail_util import (
    load_template,
    render_text_content,
    send_email,
    send_reset_email,
    send_delete_account,
)
from src.config.config import settings

settings.SMTP_HOST = "smtp.test.com"
settings.SMTP_PORT = "587"
settings.SMTP_USER = "test_user"
settings.SMTP_ACCOUNT = "test_account"
settings.SMTP_PASSWORD = "test_password"
settings.FRONTEND_URL = "https://test.frontend"


@pytest.fixture(name="mocked_template")
def mock_template() -> str:
    """Fixture providing a mock template string with placeholders."""
    return "Hello, {name}! Your token is {token}."


def test_load_template(mocker: MockerFixture, mocked_template: str) -> None:
    """Test that load_template correctly replaces placeholders in a template file."""
    mocker.patch("pathlib.Path.read_text", return_value=mocked_template)
    result: str = load_template("dummy/path", name="Sander", token="abc123")
    assert result == "Hello, Sander! Your token is abc123."


def test_render_text_content() -> None:
    """Test that render_text_content correctly replaces placeholders in a template string."""
    template: str = "Hello, {name}! Your token is {token}."
    result: str = render_text_content(template, name="Sander", token="abc123")
    assert result == "Hello, Sander! Your token is abc123."


@patch("smtplib.SMTP")
def test_send_email(mock_smtp: MagicMock) -> None:
    """Test that send_email correctly initializes and uses the SMTP server."""
    mock_smtp_instance: MagicMock = mock_smtp.return_value.__enter__.return_value
    mock_smtp_instance.starttls.return_value = None
    mock_smtp_instance.login.return_value = (235, b"OK")
    mock_smtp_instance.send_message.return_value = {}

    send_email(
        to_email="test@example.com",
        subject="Test Subject",
        html_content="<h1>HTML Content</h1>",
        text_content="Plain Text Content",
    )

    mock_smtp.assert_called_once_with("smtp.test.com", 587)
    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once_with("test_account", "test_password")
    mock_smtp_instance.send_message.assert_called_once()


@patch("src.util.mail_util.load_template")
@patch("src.util.mail_util.render_text_content")
@patch("src.util.mail_util.send_email")
def test_send_reset_email(
    mock_send_email: MagicMock,
    mock_render_text: MagicMock,
    mock_load_template: MagicMock,
) -> None:
    """Test that send_reset_email loads and renders templates correctly and sends the email."""
    mock_load_template.return_value = "<h1>HTML Reset Content</h1>"
    mock_render_text.return_value = "Plain Reset Content"

    send_reset_email(
        to_email="test@example.com",
        subject="Reset Password",
        access_token="abc123",
    )

    mock_load_template.assert_called_once_with(
        "src/templates/password_reset_email.html",
        frontend_url="https://test.frontend",
        token="abc123",
        year=datetime.datetime.now().year,
    )
    mock_render_text.assert_called_once_with(
        """Hi,
        We received a request to reset your password. Go to the link below to proceed:
        "{frontend_url}/password?access_token={token}"
        If you didn't request this, please ignore this email or contact support.
        {year} Zwaar Developers. All rights reserved.""",
        frontend_url="https://test.frontend",
        token="abc123",
        year=datetime.datetime.now().year,
    )
    mock_send_email.assert_called_once_with(
        to_email="test@example.com",
        subject="Reset Password",
        html_content="<h1>HTML Reset Content</h1>",
        text_content="Plain Reset Content",
    )


@patch("src.util.mail_util.load_template")
@patch("src.util.mail_util.render_text_content")
@patch("src.util.mail_util.send_email")
def test_send_delete_account(
    mock_send_email: MagicMock,
    mock_render_text: MagicMock,
    mock_load_template: MagicMock,
) -> None:
    """Test that send_delete_account loads and renders templates correctly and sends the email."""
    mock_load_template.return_value = "<h1>HTML Delete Content</h1>"
    mock_render_text.return_value = "Plain Delete Content"

    send_delete_account(
        to_email="test@example.com",
        subject="Delete Account",
        access_token="abc123",
    )

    mock_load_template.assert_called_once_with(
        "src/templates/delete_account_email.html",
        frontend_url="https://test.frontend",
        token="abc123",
        year=datetime.datetime.now().year,
    )
    mock_render_text.assert_called_once_with(
        """Hi,
        We received a request to delete your account. Go to the link below to proceed:
        "{frontend_url}/deletion?access_token={token}"
        If you didn't request this, please ignore this email or contact support.
        {year} Zwaar Developers. All rights reserved.""",
        frontend_url="https://test.frontend",
        token="abc123",
        year=datetime.datetime.now().year,
    )
    mock_send_email.assert_called_once_with(
        to_email="test@example.com",
        subject="Delete Account",
        html_content="<h1>HTML Delete Content</h1>",
        text_content="Plain Delete Content",
    )


@patch("smtplib.SMTP")
def test_send_email_exception(mock_smtp: MagicMock) -> None:
    """Test that send_email handles SMTP exceptions gracefully and prints an error message."""
    mock_smtp_instance: MagicMock = mock_smtp.return_value.__enter__.return_value
    mock_smtp_instance.starttls.side_effect = Exception("SMTP Error")

    with patch("builtins.print") as mock_print:
        send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<h1>HTML Content</h1>",
            text_content="Plain Text Content",
        )
        mock_print.assert_called_with("Error sending email: SMTP Error")
