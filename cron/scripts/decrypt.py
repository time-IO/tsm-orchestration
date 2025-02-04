import os

from cryptography.fernet import Fernet


def decrypt(token: str) -> str:
    key = os.environ["FERNET_ENCRYPTION_SECRET"]
    return Fernet(key).decrypt(token).decode()
