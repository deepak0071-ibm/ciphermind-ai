from cryptography.fernet import Fernet
import os


class EncryptionEngine:

    def __init__(self, key=None):

        if key is None:

            key = os.environ.get("CIPHERMIND_KEY")

            if key is None:

                key = Fernet.generate_key().decode()

                print("Generated new encryption key")

        if isinstance(key, str):
            key = key.encode()

        self.cipher = Fernet(key)


    def encrypt(self, text):

        return self.cipher.encrypt(text.encode()).decode()


    def decrypt(self, encrypted_text):

        return self.cipher.decrypt(encrypted_text.encode()).decode()
