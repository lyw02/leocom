import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Shared secret key (should be securely exchanged between client and server)
SECRET_KEY = b"supersecretkey12"  # 16 bytes for AES-128

# Encrypt data using AES-GCM
def encrypt_data(data, key):
    iv = os.urandom(12)  # Generate a random 12-byte IV
    encryptor = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()).encryptor()
    ciphertext = encryptor.update(data.encode()) + encryptor.finalize()
    return iv + encryptor.tag + ciphertext  # Return IV, tag, and ciphertext together

# Decrypt data using AES-GCM
def decrypt_data(encrypted_data, key):
    iv = encrypted_data[:12]  # First 12 bytes are the IV
    tag = encrypted_data[12:28]  # Next 16 bytes are the GCM tag
    ciphertext = encrypted_data[28:]  # Remaining bytes are the ciphertext
    decryptor = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()).decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()
