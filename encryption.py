from cryptography.fernet import Fernet
import base64
import hashlib

class EncryptionEngine:

    def __init__(self, key):
        key_bytes = hashlib.sha256(key.encode()).digest()
        self.key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(self.key)

    def encrypt(self, text):
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, encrypted):
        return self.cipher.decrypt(encrypted.encode()).decode()
