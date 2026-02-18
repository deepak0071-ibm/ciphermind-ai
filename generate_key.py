from cryptography.fernet import Fernet

key = Fernet.generate_key().decode()

print("\nYour CipherMind Encryption Key:\n")
print(key)
