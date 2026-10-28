import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def get_encryption_key():
    encoded_key = os.getenv("ENCRYPTION_KEY")

    if not encoded_key:
        raise RuntimeError("ENCRYPTION_KEY is not configured.")

    key = base64.b64decode(encoded_key)

    if len(key) != 32:
        raise RuntimeError("ENCRYPTION_KEY must be a 32-byte AES key.")

    return key


def encrypt_file(file_data):
    key = get_encryption_key()

    nonce = os.urandom(12)

    aesgcm = AESGCM(key)
    encrypted_data = aesgcm.encrypt(
        nonce,
        file_data,
        None
    )

    return encrypted_data, nonce