from cryptography.fernet import Fernet

class EncryptionEngine:

    def __init__(self, key=None):
        if key is None:
            key = Fernet.generate_key()

        self.key = key
        self.cipher = Fernet(self.key)

    def encrypt(self, text):
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text):
        return self.cipher.decrypt(encrypted_text.encode()).decode()
