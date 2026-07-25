from abc import ABC, abstractmethod

class ISecretsManager(ABC):
    """Port interface for secure key encryption and decryption at rest."""
    
    @abstractmethod
    def encrypt(self, plaintext: str) -> str:
        """Encrypts a plaintext key using cryptographic ciphers before database storage.
        
        Args:
            plaintext (str): Plaintext secret token.
            
        Returns:
            str: Base64 or encrypted ciphertext string.
        """
        pass

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str:
        """Decrypts ciphertext credentials back into plaintext strictly in-memory during completions.
        
        Args:
            ciphertext (str): Cryptographic ciphertext token.
            
        Returns:
            str: Plaintext secret credential.
        """
        pass
