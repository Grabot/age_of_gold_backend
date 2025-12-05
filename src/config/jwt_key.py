import base64
from typing import cast

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from src.config.config import settings

private_key_passphrase = settings.PRIVATE_KEY_PASSPHRASE

base64_pem = settings.JWT_PEM

base64_bytes_pem = base64_pem.encode("utf-8")
pem_bytes = base64.b64decode(base64_bytes_pem)

private_key = serialization.load_pem_private_key(
    pem_bytes,
    password=private_key_passphrase.encode("utf-8"),
    backend=default_backend(),
)

jwt_public_key = cast(ec.EllipticCurvePublicKey, private_key.public_key())
jwt_private_key = cast(ec.EllipticCurvePrivateKey, private_key)
