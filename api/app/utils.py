import string
import secrets
import paramiko
import io
import re
import uuid
from pathlib import Path
from config import settings


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


def get_ssh_priv_key(filepath, priv_key):
    if Path(filepath).is_file():
        try:
            return Path(filepath).read_text().strip()
        except Exception as e:
            raise ValueError(f"Invalid SSH key: {e}")
    return priv_key
