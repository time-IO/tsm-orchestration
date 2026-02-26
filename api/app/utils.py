import string
import secrets
import paramiko
import io
import re
import uuid


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
    name = permisison_group_name
    if readonly:
        name = "ro_" + permisison_group_name
    return re.sub("[^a-z0-9_]+", "", f"{name[0:30].lower()}_{uuid.uuid4()}")
