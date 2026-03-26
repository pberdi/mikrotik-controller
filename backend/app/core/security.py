"""
Security utilities for authentication and authorization.

This module provides JWT token management, password hashing, and
authentication utilities for the FastAPI application.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import bcrypt
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext

from ..config import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTManager:
    """
    JWT token management for authentication.
    
    This class handles creation, validation, and decoding of JWT tokens
    for user authentication and authorization.
    """
    
    def __init__(self):
        """Initialize JWT manager with configuration."""
        self.secret_key = settings.security.secret_key
        self.algorithm = settings.security.algorithm
        self.access_token_expire_minutes = settings.security.access_token_expire_minutes
        self.refresh_token_expire_days = settings.security.refresh_token_expire_days
    
    def create_access_token(
        self, 
        subject: Union[str, Any], 
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[dict] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            subject: Token subject (usually user ID).
            expires_delta: Custom expiration time. If None, uses default.
            additional_claims: Additional claims to include in token.
            
        Returns:
            str: Encoded JWT token.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        # Standard JWT claims
        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access"
        }
        
        # Add additional claims if provided
        if additional_claims:
            payload.update(additional_claims)
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created access token for subject: {subject}")
            return token
        except Exception as e:
            logger.error(f"Failed to create access token: {e}")
            raise Exception(f"Token creation failed: {e}")
    
    def create_refresh_token(
        self, 
        subject: Union[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token.
        
        Args:
            subject: Token subject (usually user ID).
            expires_delta: Custom expiration time. If None, uses default.
            
        Returns:
            str: Encoded JWT refresh token.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )
        
        payload = {
            "sub": str(subject),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh"
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.debug(f"Created refresh token for subject: {subject}")
            return token
        except Exception as e:
            logger.error(f"Failed to create refresh token: {e}")
            raise Exception(f"Refresh token creation failed: {e}")
    
    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify.
            token_type: Expected token type ("access" or "refresh").
            
        Returns:
            dict: Decoded token payload.
            
        Raises:
            JWTError: If token is invalid, expired, or wrong type.
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get("type") != token_type:
                raise JWTError(f"Invalid token type. Expected {token_type}")
            
            logger.debug(f"Successfully verified {token_type} token")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise JWTError("Token has expired")
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            raise JWTError(f"Invalid token: {e}")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise JWTError(f"Token verification failed: {e}")
    
    def decode_token_without_verification(self, token: str) -> dict:
        """
        Decode token without verification (for debugging/inspection).
        
        Args:
            token: JWT token to decode.
            
        Returns:
            dict: Decoded token payload.
            
        Warning:
            This method does not verify token signature or expiration.
            Use only for debugging or inspection purposes.
        """
        try:
            payload = jwt.decode(
                token, 
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Failed to decode token: {e}")
            raise Exception(f"Token decoding failed: {e}")
    
    def get_token_subject(self, token: str) -> Optional[str]:
        """
        Extract subject from token without full verification.
        
        Args:
            token: JWT token.
            
        Returns:
            str: Token subject if extractable, None otherwise.
        """
        try:
            payload = self.decode_token_without_verification(token)
            return payload.get("sub")
        except Exception:
            return None


# Global JWT manager instance
jwt_manager = JWTManager()


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """
    Create JWT access token using global manager.
    
    Args:
        subject: Token subject (usually user ID).
        expires_delta: Custom expiration time.
        additional_claims: Additional claims to include.
        
    Returns:
        str: Encoded JWT access token.
    """
    return jwt_manager.create_access_token(subject, expires_delta, additional_claims)


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token using global manager.
    
    Args:
        subject: Token subject (usually user ID).
        expires_delta: Custom expiration time.
        
    Returns:
        str: Encoded JWT refresh token.
    """
    return jwt_manager.create_refresh_token(subject, expires_delta)


def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verify JWT token using global manager.
    
    Args:
        token: JWT token to verify.
        token_type: Expected token type.
        
    Returns:
        dict: Decoded token payload.
        
    Raises:
        JWTError: If token is invalid.
    """
    return jwt_manager.verify_token(token, token_type)


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    
    Args:
        password: Plain text password.
        
    Returns:
        str: Hashed password.
        
    Raises:
        ValueError: If password is too short.
    """
    if len(password) < settings.security.password_min_length:
        raise ValueError(
            f"Password must be at least {settings.security.password_min_length} characters long"
        )
    
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        logger.debug("Password hashed successfully")
        return hashed.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Password hashing failed: {e}")
        raise Exception(f"Password hashing failed: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    
    Args:
        plain_password: Plain text password to verify.
        hashed_password: Stored password hash.
        
    Returns:
        bool: True if password matches, False otherwise.
    """
    try:
        # Verify password using bcrypt
        is_valid = bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
        
        logger.debug(f"Password verification result: {is_valid}")
        return is_valid
        
    except Exception as e:
        logger.error(f"Password verification failed: {e}")
        return False


def generate_password_reset_token(user_id: str) -> str:
    """
    Generate password reset token.
    
    Args:
        user_id: User ID for password reset.
        
    Returns:
        str: Password reset token (valid for 1 hour).
    """
    expires_delta = timedelta(hours=1)
    additional_claims = {"type": "password_reset"}
    
    return jwt_manager.create_access_token(
        subject=user_id,
        expires_delta=expires_delta,
        additional_claims=additional_claims
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and extract user ID.
    
    Args:
        token: Password reset token.
        
    Returns:
        str: User ID if token is valid, None otherwise.
    """
    try:
        payload = jwt_manager.verify_token(token, token_type="access")
        
        # Verify it's a password reset token
        if payload.get("type") != "password_reset":
            return None
        
        return payload.get("sub")
        
    except JWTError:
        return None


def create_api_key_token(user_id: str, key_name: str, expires_days: int = 365) -> str:
    """
    Create long-lived API key token.
    
    Args:
        user_id: User ID for API key.
        key_name: Name/description of the API key.
        expires_days: Expiration in days.
        
    Returns:
        str: API key token.
    """
    expires_delta = timedelta(days=expires_days)
    additional_claims = {
        "type": "api_key",
        "key_name": key_name
    }
    
    return jwt_manager.create_access_token(
        subject=user_id,
        expires_delta=expires_delta,
        additional_claims=additional_claims
    )