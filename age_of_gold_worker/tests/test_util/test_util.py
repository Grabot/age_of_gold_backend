import pytest
from unittest.mock import MagicMock, patch
from age_of_gold_worker.age_of_gold_worker.util.util import worker_upload_image


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Fixture for a mocked S3 client."""
    return MagicMock()


@patch("age_of_gold_worker.age_of_gold_worker.util.s3_client.get_s3_client")
def test_worker_upload_image(
    mock_get_s3_client: MagicMock, mock_s3_client: MagicMock
) -> None:
    """Test that worker_upload_image uploads the image to S3 correctly."""
    mock_get_s3_client.return_value = mock_s3_client

    test_avatar_bytes = b"fake_image_data"
    test_bucket = "test-bucket"
    test_s3_key = "test-key.png"

    worker_upload_image(test_avatar_bytes, test_bucket, test_s3_key)

    mock_get_s3_client.assert_called_once()
    mock_s3_client.upload_fileobj.assert_called_once()

    args, kwargs = mock_s3_client.upload_fileobj.call_args

    buffer = args[0]
    buffer.seek(0)
    buffer_content = buffer.read()
    assert buffer_content == test_avatar_bytes

    assert args[1] == test_bucket
    assert args[2] == test_s3_key
    assert kwargs["ExtraArgs"]["ContentType"] == "image/png"


@patch("age_of_gold_worker.age_of_gold_worker.util.s3_client.get_s3_client")
def test_worker_upload_image_empty_data(
    mock_get_s3_client: MagicMock, mock_s3_client: MagicMock
) -> None:
    """Test that worker_upload_image handles empty data."""
    mock_get_s3_client.return_value = mock_s3_client

    worker_upload_image(b"", "test-bucket", "test-key.png")

    mock_s3_client.upload_fileobj.assert_called_once()
    args, _ = mock_s3_client.upload_fileobj.call_args
    buffer = args[0]
    buffer.seek(0)
    assert buffer.read() == b""
