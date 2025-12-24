from typing import Any
from unittest.mock import patch, MagicMock
from botocore.client import Config
from age_of_gold_worker.age_of_gold_worker.util.s3_client import get_s3_client
from age_of_gold_worker.age_of_gold_worker.worker_settings import worker_settings


@patch("boto3.client")
def test_get_s3_client_singleton(mock_boto3_client: Any) -> None:
    """Test that get_s3_client returns the same instance on repeated calls."""
    mock_client = MagicMock()
    mock_boto3_client.return_value = mock_client

    client1 = get_s3_client()

    args, kwargs = mock_boto3_client.call_args
    assert args == ("s3",)
    assert kwargs["endpoint_url"] == worker_settings.S3_ENDPOINT
    assert kwargs["aws_access_key_id"] == worker_settings.S3_ACCESS_KEY
    assert kwargs["aws_secret_access_key"] == worker_settings.S3_SECRET_KEY
    assert kwargs["region_name"] == "eu-central-1"
    assert isinstance(kwargs["config"], Config)
    assert kwargs["config"].signature_version == "s3v4"

    client2 = get_s3_client()

    assert client1 == client2

    mock_boto3_client.assert_called_once()
