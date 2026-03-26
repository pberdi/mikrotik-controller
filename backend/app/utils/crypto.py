"""
Cryptographic utilities for secure credential storage.

This module provides the SecretVault class for encrypting and decrypting
sensitive data using AES-256 encryption with PBKDF2 key derivation.
"""

import base64
import hashlib
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from ..config import settings

logger = logging.getLogger(__name__)


class SecretVault:
    """
    Secure credential storage using AES-256 encryption.
    
    This class provides methods for encrypting and decrypting sensitive data
    such as device credentials using industry-standard encryption practices.
    """
    
    def __init__(self, master_secret: Optional[str] = None):
        """
        Initialize SecretVault with master secret.
        
        Args:
            master_secret: Master secret for key derivation. If None, uses config.
            
        Raises:
            ValueError: If master secret is not provided or too short.
        """
        self._master_secret = master_secret or settings.security.encryption_key
        
        if not self._master_secret:
            raise ValueError("Master secret is required for SecretVault")
        
        if len(self._master_secret) < 32:
            raise ValueError("Master secret must be at least 32 characters long")
        
        # Generate a fixed salt from the master secret for consistent key derivation
        # In production, you might want to use a separate salt storage mechanism
        self._salt = hashlib.sha256(self._master_secret.encode()).digest()[:16]
        
        # Derive encryption key using PBKDF2
        self._encryption_key = self._derive_key(self._salt)
        self._fernet = Fernet(self._encryption_key)
        
        logger.debug("SecretVault initialized successfully")
    
    def _derive_key(self, salt: bytes) -> bytes:
        """
        Derive encryption key from master secret using PBKDF2.
        
        Args:
            salt: Salt bytes for key derivation.
            
        Returns:
            bytes: Base64-encoded encryption key suitable for Fernet.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits for AES-256
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )
        
        key = kdf.derive(self._master_secret.encode())
        return base64.urlsafe_b64encode(key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            str: Base64-encoded encrypted data.
            
        Raises:
            ValueError: If plaintext is empty.
            Exception: If encryption fails.
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty plaintext")
        
        try:
            # Convert string to bytes
            plaintext_bytes = plaintext.encode('utf-8')
            
            # Encrypt using Fernet (includes timestamp and integrity check)
            encrypted_bytes = self._fernet.encrypt(plaintext_bytes)
            
            # Return base64-encoded string for database storage
            encrypted_str = base64.b64encode(encrypted_bytes).decode('ascii')
            
            logger.debug("Successfully encrypted data")
            return encrypted_str
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise Exception(f"Failed to encrypt data: {e}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted string.
        
        Args:
            encrypted_data: Base64-encoded encrypted data.
            
        Returns:
            str: Decrypted plaintext string.
            
        Raises:
            ValueError: If encrypted_data is empty or invalid.
            Exception: If decryption fails.
        """
        if not encrypted_data:
            raise ValueError("Cannot decrypt empty data")
        
        try:
            # Decode base64 string to bytes
            encrypted_bytes = base64.b64decode(encrypted_data.encode('ascii'))
            
            # Decrypt using Fernet (includes timestamp and integrity verification)
            plaintext_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Convert bytes back to string
            plaintext = plaintext_bytes.decode('utf-8')
            
            logger.debug("Successfully decrypted data")
            return plaintext
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise Exception(f"Failed to decrypt data: {e}")
    
    def rotate_key(self, new_master_secret: str) -> 'SecretVault':
        """
        Create new SecretVault instance with rotated key.
        
        This method creates a new SecretVault with a different master secret.
        Use this for key rotation by decrypting with old vault and encrypting
        with new vault.
        
        Args:
            new_master_secret: New master secret for key derivation.
            
        Returns:
            SecretVault: New vault instance with rotated key.
        """
        return SecretVault(new_master_secret)
    
    def verify_integrity(self, plaintext: str, encrypted_data: str) -> bool:
        """
        Verify that encrypted data decrypts to expected plaintext.
        
        Args:
            plaintext: Expected plaintext.
            encrypted_data: Encrypted data to verify.
            
        Returns:
            bool: True if integrity check passes, False otherwise.
        """
        try:
            decrypted = self.decrypt(encrypted_data)
            return decrypted == plaintext
        except Exception:
            return False
    
    def __del__(self):
        """Clean up sensitive data on destruction."""
        # Clear sensitive attributes
        if hasattr(self, '_master_secret'):
            self._master_secret = None
        if hasattr(self, '_encryption_key'):
            self._encryption_key = None
        if hasattr(self, '_salt'):
            self._salt = None


# Global SecretVault instance
_secret_vault: Optional[SecretVault] = None


def get_secret_vault() -> SecretVault:
    """
    Get global SecretVault instance.
    
    Returns:
        SecretVault: Global vault instance.
        
    Raises:
        RuntimeError: If vault initialization fails.
    """
    global _secret_vault
    
    if _secret_vault is None:
        try:
            _secret_vault = SecretVault()
        except Exception as e:
            logger.error(f"Failed to initialize SecretVault: {e}")
            raise RuntimeError(f"SecretVault initialization failed: {e}")
    
    return _secret_vault


def encrypt_credential(plaintext: str) -> str:
    """
    Convenience function to encrypt credential using global vault.
    
    Args:
        plaintext: Credential to encrypt.
        
    Returns:
        str: Encrypted credential.
    """
    vault = get_secret_vault()
    return vault.encrypt(plaintext)


def decrypt_credential(encrypted_data: str) -> str:
    """
    Convenience function to decrypt credential using global vault.
    
    Args:
        encrypted_data: Encrypted credential.
        
    Returns:
        str: Decrypted credential.
    """
    vault = get_secret_vault()
    return vault.decrypt(encrypted_data)


def verify_credential_integrity(plaintext: str, encrypted_data: str) -> bool:
    """
    Convenience function to verify credential integrity using global vault.
    
    Args:
        plaintext: Expected plaintext.
        encrypted_data: Encrypted data to verify.
        
    Returns:
        bool: True if integrity check passes.
    """
    vault = get_secret_vault()
    return vault.verify_integrity(plaintext, encrypted_data)