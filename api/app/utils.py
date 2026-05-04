import string
import secrets
import paramiko
import io
import re
import uuid
from config import settings
import os
import hashlib
import base64


def generate_password(length: int):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def generate_keypair():
    key = paramiko.RSAKey.generate(2048)

    private_key_io = io.StringIO()
    key.write_private_key(private_key_io)
    private_key = private_key_io.getvalue()
    public_key = f"{key.get_name()} {key.get_base64()}"

    return private_key, public_key


def create_db_username(permisison_group_name: str, readonly: bool = False):
    # The permission group names consist of <name of virtual organization (vo)>:<name of group>
    # To have a visual separator between vo and group we replace the : (colon) by _ (underscore)
    vo, group = permisison_group_name.split(":")
    name = f"{vo[:10]}_{group}"
    if readonly:
        name = "ro_" + name
    return re.sub("[^a-z0-9_]+", "", f"{name[0:30].lower()}_{uuid.uuid4()}")


def get_connection_string_secure(db, readonly: bool = False):
    if db:
        usr = db.read_only_username if readonly else db.username

        return f"postgresql://{usr}@{settings.POSTGRES_SERVER}/{settings.POSTGRES_DB}"
    return "-"


def hash_password(
    password: str,
    hasher: str = "pbkdf2_sha256",
    iterations: int = 260000,
    salt: bytes = None,
) -> str:
    """
    Hash a password using PBKDF2 (equivalent to Django's make_password with PBKDF2 hasher).

    Returns a string in Django-compatible format: 'algorithm$iterations$salt$hash'
    """
    if hasher != "pbkdf2_sha256":
        raise ValueError("Only 'pbkdf2_sha256' is supported in this implementation")

    if salt is None:
        salt = os.urandom(16)  # Django uses 16-byte random salt

    # Ensure password is bytes
    password_bytes = password.encode("utf-8")

    # PBKDF2-HMAC-SHA256
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password_bytes, salt, iterations)

    # Encode salt and hash in base64 (Django uses base64 without padding)
    salt_b64 = base64.b64encode(salt).rstrip(b"=").decode("ascii")
    hash_b64 = base64.b64encode(hash_bytes).rstrip(b"=").decode("ascii")

    return f"pbkdf2_sha256${iterations}${salt_b64}${hash_b64}"
