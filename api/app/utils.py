import string
import secrets
import paramiko
import io


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
