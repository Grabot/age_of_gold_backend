import base64
import os
from typing import cast
from cryptography.fernet import Fernet

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def generate_pem_key(private_key_hex: str, encrypt: bool, passphrase: bytes) -> str:
    """
    Generate a PEM-encoded EC private key from a private scalar (hex).

    Args:
        private_key_hex: Hex string representing the private scalar `d`.
        encrypt: If True, encrypt the PEM with `passphrase`.
        passphrase: Passphrase for PEM encryption (required if `encrypt=True`).

    Returns:
        PEM-encoded private key as a UTF-8 string.
    """
    curve = ec.SECP256R1()

    private_key = ec.derive_private_key(
        int(private_key_hex, 16), curve, default_backend()
    )

    encryption = (
        serialization.BestAvailableEncryption(passphrase)
        if encrypt and passphrase
        else serialization.NoEncryption()
    )

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=encryption,
    )
    return pem.decode("utf-8")


def generate_secure_private_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1(), default_backend())


def generate_pem() -> str:
    """Generate a PEM-encoded EC private key."""
    private_key = generate_secure_private_key()
    private_key_hex = f"{private_key.private_numbers().private_value:x}"
    private_key_passphrase = os.getenv("PRIVATE_KEY_PASSPHRASE", None)
    if not private_key_passphrase:
        raise ValueError("PRIVATE_KEY_PASSPHRASE environment variable is not set")
    pem = generate_pem_key(
        private_key_hex=private_key_hex,
        encrypt=True,
        passphrase=private_key_passphrase.encode("utf-8"),
    )
    return pem


def generate_encryption_key() -> None:
    key = Fernet.generate_key()
    print("Save this key:", key.decode())


if __name__ == "__main__":
    # Generate a PEM-encoded EC private key using a random private_key_hex
    # Convert it to bytes and do a base64 encoding and print that value
    # The single line of base64 encoded string is the value of JWT_PEM in the .env
    # Decode it and use it to get the private key (to test that it works)
    generate_encryption_key()
    private_key_passphrase = os.getenv("PRIVATE_KEY_PASSPHRASE", None)
    if not private_key_passphrase:
        raise ValueError("PRIVATE_KEY_PASSPHRASE environment variable is not set")
    pem: str = generate_pem()
    pem_bytes = pem.encode("utf-8")
    base64_bytes = base64.b64encode(pem_bytes)
    base64_string = base64_bytes.decode("utf-8")

    print(base64_string)

    base64_bytes = base64_string.encode("utf-8")

    pem_bytes = base64.b64decode(base64_bytes)
    _ = cast(
        ec.EllipticCurvePrivateKey,
        serialization.load_pem_private_key(
            pem_bytes,
            password=private_key_passphrase.encode("utf-8"),
            backend=default_backend(),
        ),
    )
