"""
crypto_utils.py - Cryptographic Utilities for Pixel Steganography
==================================================================
Provides robust, password-based authenticated encryption and decryption
using PBKDF2 key derivation and Fernet (AES-128-CBC + HMAC-SHA256).

Security Architecture:
----------------------
1. Key Derivation:
   - Algorithm: PBKDF2 (Password-Based Key Derivation Function 2)
   - Hash Function: HMAC-SHA256
   - Iterations: 480,000 (Aligned with OWASP recommendations)
   - Salt: 16 cryptographically secure random bytes generated per encryption (os.urandom).
   
2. Encryption & Integrity:
   - Fernet symmetric encryption: AES-128 in CBC mode with PKCS7 padding.
   - HMAC with SHA-256 for ciphertext authentication and tamper resistance.
   - Precludes bit-flipping attacks and provides immediate feedback upon wrong password.

3. Payload Container:
   - Formatted as `ENC:v1:<base64(salt + token)>`
   - Self-contained, portable, and easily distinguished from plaintext messages.
"""

import base64
import os
from typing import Tuple
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Constants
SALT_SIZE = 16  # 128-bit salt
PBKDF2_ITERATIONS = 480000  # OWASP recommendation for PBKDF2-HMAC-SHA256
PAYLOAD_PREFIX = "ENC:v1:"


class CryptoError(Exception):
    """Base exception for cryptographic errors."""
    pass


class InvalidPasswordError(CryptoError):
    """Raised when decryption fails due to an incorrect password or tampering."""
    pass


class InvalidPayloadError(CryptoError):
    """Raised when the payload format is invalid or corrupted."""
    pass


def derive_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """
    Derive a 32-byte URL-safe base64-encoded key from a user password and salt
    using PBKDF2HMAC-SHA256.

    Args:
        password: User-provided plaintext password string.
        salt: 16-byte random cryptographic salt.
        iterations: Number of PBKDF2 computation cycles.

    Returns:
        32-byte URL-safe base64-encoded Fernet key.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=iterations,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
    return key


def encrypt_message(plaintext: str, password: str) -> str:
    """
    Encrypt a plaintext string using a user password.
    
    Workflow:
    1. Generate a random 16-byte cryptographic salt.
    2. Derive a 256-bit symmetric key via PBKDF2-HMAC-SHA256.
    3. Encrypt the UTF-8 plaintext using Fernet (AES-CBC + HMAC).
    4. Combine salt + Fernet token and base64-encode.
    5. Prepend version prefix `ENC:v1:`.

    Args:
        plaintext: The secret message to encrypt.
        password: The user password for key derivation.

    Returns:
        Formatted encrypted payload string: `ENC:v1:<base64_data>`.
    """
    if not plaintext:
        raise ValueError("Plaintext message cannot be empty.")
    if not password:
        raise ValueError("Password cannot be empty for encryption.")

    # Generate fresh random salt
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    fernet = Fernet(key)

    # Encrypt the plaintext (Fernet produces bytes containing IV + ciphertext + HMAC)
    token = fernet.encrypt(plaintext.encode("utf-8"))

    # Bundle salt + token together
    packaged_bytes = salt + token
    encoded_package = base64.b64encode(packaged_bytes).decode("ascii")

    return f"{PAYLOAD_PREFIX}{encoded_package}"


def decrypt_message(encrypted_payload: str, password: str) -> str:
    """
    Decrypt a previously encrypted payload string using the user password.

    Workflow:
    1. Verify payload prefix format (`ENC:v1:`).
    2. Base64-decode the packaged bytes.
    3. Extract the 16-byte salt and the remaining Fernet token.
    4. Re-derive the key using the extracted salt and provided password.
    5. Decrypt and verify HMAC using Fernet.

    Args:
        encrypted_payload: Formatted ciphertext string (`ENC:v1:<base64_data>`).
        password: User password used during encryption.

    Returns:
        Decrypted original plaintext string.

    Raises:
        InvalidPayloadError: If the payload is malformed or improperly formatted.
        InvalidPasswordError: If the password is wrong or data is corrupted/tampered.
    """
    if not encrypted_payload:
        raise ValueError("Encrypted payload cannot be empty.")
    if not password:
        raise ValueError("Password cannot be empty for decryption.")

    if not is_encrypted(encrypted_payload):
        raise InvalidPayloadError("Payload is not a valid encrypted message (missing prefix).")

    # Strip prefix and decode base64
    raw_encoded = encrypted_payload[len(PAYLOAD_PREFIX):]
    try:
        packaged_bytes = base64.b64decode(raw_encoded.encode("ascii"))
    except Exception as e:
        raise InvalidPayloadError(f"Corrupted base64 payload: {e}")

    if len(packaged_bytes) <= SALT_SIZE:
        raise InvalidPayloadError("Payload is truncated or missing cipher data.")

    # Split salt and token
    salt = packaged_bytes[:SALT_SIZE]
    token = packaged_bytes[SALT_SIZE:]

    # Derive key and attempt decryption
    try:
        key = derive_key(password, salt)
        fernet = Fernet(key)
        decrypted_bytes = fernet.decrypt(token)
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        raise InvalidPasswordError("Decryption failed. Incorrect password or data has been altered.")
    except Exception as e:
        raise CryptoError(f"Unexpected decryption error: {e}")


def is_encrypted(payload: str) -> bool:
    """
    Check if a payload string matches the encrypted payload format.

    Args:
        payload: String to inspect.

    Returns:
        True if the payload starts with `ENC:v1:`, False otherwise.
    """
    return isinstance(payload, str) and payload.startswith(PAYLOAD_PREFIX)
