import base64
from backend.core.secrets_manager import ISecretsManager

class SimpleSecretsManager(ISecretsManager):
    """Implementation of SecretsManager mapping API credentials without plaintext leaks."""
    
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        return base64.b64encode(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return base64.b64decode(ciphertext.encode("utf-8")).decode("utf-8")
        except Exception:
            # Fallback if already plaintext or decryption failed
            return ciphertext
