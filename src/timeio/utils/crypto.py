#!/usr/bin/env python3
import os

from cryptography.fernet import Fernet
from .common import get_envvar as _get_envvar


def get_crypt_key() -> str:
    return _get_envvar("FERNET_ENCRYPTION_SECRET")


def encrypt(data: str, key: str) -> str:
    return Fernet(key).encrypt(data.encode()).decode()


def decrypt(token: str, key: str):
    return Fernet(key).decrypt(token).decode()
