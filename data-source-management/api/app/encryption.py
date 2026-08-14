from cryptography.fernet import Fernet
from config import settings
from sqlalchemy import TypeDecorator, TEXT
import logging

logger = logging.getLogger("app.encryption")


class EncryptionService:
    def __init__(self, key: bytes | None = None):
        if key is None:
            key = settings.FERNET_ENCRYPTION_SECRET
        self.cipher = Fernet(key)

    # Encrypt string
    def encrypt(self, string: str) -> str:
        encrypted_bytes = self.cipher.encrypt(string.encode())
        return encrypted_bytes.decode()

    # Decrypt string
    def decrypt(self, encrypted_string: str) -> str:
        decrypted_bytes = self.cipher.decrypt(encrypted_string.encode())
        return decrypted_bytes.decode()


encryption_service = EncryptionService()


class EncryptedType(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts text."""

    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # value comes from Python → to database
        return encryption_service.encrypt(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # value comes from database → to Python
        return encryption_service.decrypt(value)
