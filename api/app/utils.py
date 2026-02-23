import string
import secrets


def generate_password(length: int):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))
