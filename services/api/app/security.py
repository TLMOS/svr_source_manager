import os
from base64 import urlsafe_b64encode as b64e, urlsafe_b64decode as b64d

import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def _derive_key(password: bytes, salt: bytes) -> bytes:
    """
    Derive a key from a password using PBKDF2HMAC.

    Parameters:
    - password (bytes): Password to derive the key from
    - salt (bytes): Salt to use for the key derivation

    Returns:
    - bytes: Derived key
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    return b64e(kdf.derive(password))


def encrypt_secret(secret: str, password: str) -> str:
    """
    Encrypt a secret with a password using Fernet.

    Parameters:
    - secret (str): Secret to encrypt
    - password (str): Password to use for encryption

    Returns:
    - str: Encrypted secret
    """
    secret = secret.encode()
    salt = os.urandom(16)
    key = _derive_key(password.encode(), salt)
    return b64e(b'%b%b' % (salt, b64d(Fernet(key).encrypt(secret)))).decode()


def decrypt_secret(secret: str, password: str) -> str:
    """
    Decrypt a secret with a password using Fernet.

    Parameters:
    - secret (str): Secret to decrypt
    - password (str): Password to use for decryption

    Returns:
    - str: Decrypted secret
    """
    secret = secret.encode()
    decoded = b64d(secret)
    salt, secret = decoded[:16], b64e(decoded[16:])
    key = _derive_key(password.encode(), salt)
    return Fernet(key).decrypt(secret).decode()


def verify_secret(plain_secret: str, hashed_secret: str) -> bool:
    """
    Verify a secret against a hash using slow hashing.

    Args:
    - plain_secret (str): Plain secret
    - hashed_secret (str): Secret hashed with bcrypt

    Returns:
    - bool: True if secret is correct, False otherwise
    """
    return bcrypt.checkpw(plain_secret.encode(), hashed_secret.encode())


def hash_secret(secret) -> str:
    """
    Get a hash of a secret using bcrypt.

    Args:
    - secret (str): Secret to hash

    Returns:
    - str: Hashed secret
    """
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()
