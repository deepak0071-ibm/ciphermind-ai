from cryptography.fernet import Fernet
import os


class EncryptionEngine:

    def __init__(self):

        key = os.environ.get("CIPHERMIND_KEY")

        # Generate persistent key if not exists
        if key is None:

            key = Fernet.generate_key().decode()

            print("Generated temporary encryption key:", key)

        if isinstance(key, str):
            key = key.encode()

        self.cipher = Fernet(key)


    def encrypt(self, text):

        if not text:
            raise Exception("No text provided")

        return self.cipher.encrypt(text.encode()).decode()


    def decrypt(self, encrypted_text):

        return self.cipher.decrypt(encrypted_text.encode()).decode()
