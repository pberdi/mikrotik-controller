"""
Logging configuration for the application.

This module provides structured logging with JSON formatting for production
and sensitive data masking for security.
"""

import json
import logging
import re
import sys
from datetime import datetime
from typing import Any, Dict

from ..config import settings


class SensitiveDataFilter(logging.Filter):
    """
    Filter to mask sensitive data in log records.
    
    This filter automatically masks common sensitive patterns like
    passwords, tokens, and API keys in log messages.
    """
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = [
        # Password patterns
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'password'),
        (re.compile(r'passwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'passwd'),
        (re.compile(r'pwd["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'pwd'),
        
        # Token patterns
        (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'token'),
        (re.compile(r'access_token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'access_token'),
        (re.compile(r'refresh_token["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'refresh_token'),
        
        # API key patterns
        (re.compile(r'api_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'api_key'),
        (re.compile(r'apikey["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'apikey'),
        (re.compile(r'key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'key'),
        
        # Secret patterns
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'secret'),
        (re.compile(r'secret_key["\']?\s*[:=]\s*["\']?([^"\'\s,}]+)', re.IGNORECASE), 'secret_key'),
        
        # Authorization header
        (re.compile(r'authorization["\']?\s*[:=]\s*["\']?bearer\s+([^"\'\s,}]+)', re.IGNORECASE), 'authorization'),
        
        # Credit card patterns (basic)
        (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), 'credit_card'),
        
        # Email patterns in sensitive contexts
        (re.compile(r'email["\']?\s*[:=]\s*["\']?([^"\'\s,}]+@[^"\'\s,}]+)', re.IGNORECASE), 'email'),
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to mask sensitive data.
        
        Args:
            record: Log record to filter.
            
        Returns:
            bool: Always True (don't filter out records).
        """
        # Mask sensitive data in the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._mask_sensitive_data(str(record.msg))
        
        # Mask sensitive data in arguments
        if hasattr(record, 'args') and record.args:
            masked_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    masked_args.append(self._mask_sensitive_data(arg))
                else:
                    masked_args.append(arg)
            record.args = tuple(masked_args)
        
        return True
    
    def _mask_sensitive_data(self, text: str) -> str:
        """
        Mask sensitive data in text.
        
        Args:
            text: Text to mask.
            
        Returns:
            str: Text with sensitive data masked.
        """
        for pattern, field_name in self.SENSITIVE_PATTERNS:
            if field_name == 'credit_card':
                # Special handling for credit cards - mask middle digits
                text = pattern.sub(lambda m: m.group(0)[:4] + '*' * 8 + m.group(0)[-4:], text)
            elif field_name == 'email':
                # Special handling for emails - mask username part
                text = pattern.sub(lambda m: f'{field_name}="***@{m.group(1).split("@")[1]}"', text)
            else:
                # Standard masking - replace with ***MASKED***
                text = pattern.sub(f'{field_name}="***MASKED***"', text)
        
        return text


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Formats log records as JSON for better parsing and analysis
    in production environments.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format.
            
        Returns:
            str: JSON-formatted log record.
        """
        # Create log entry dictionary
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from the record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry["extra"] = extra_fields
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'tenant_id'):
            log_entry["tenant_id"] = record.tenant_id
        
        return json.dumps(log_entry, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for development logging.
    
    Adds colors to log levels for better readability in development.
    """
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.
        
        Args:
            record: Log record to format.
            
        Returns:
            str: Colored log record.
        """
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{level_color}{record.levelname}{self.RESET}"
        
        # Format the record
        formatted = super().format(record)
        
        return formatted


def setup_logging() -> None:
    """
    Setup application logging configuration.
    
    Configures logging based on the application environment and settings.
    """
    # Get log level from settings
    log_level = getattr(logging, settings.app.log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    console_handler.addFilter(sensitive_filter)
    
    # Choose formatter based on environment
    if settings.app.environment == "production":
        # Use JSON formatter for production
        formatter = JSONFormatter()
    else:
        # Use colored formatter for development
        formatter = ColoredFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    configure_logger_levels()
    
    # Log configuration completion
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {settings.app.environment} environment")


def configure_logger_levels() -> None:
    """
    Configure log levels for specific loggers.
    
    Sets appropriate log levels for third-party libraries and
    application components.
    """
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)
    
    # Set application logger levels
    logging.getLogger("app").setLevel(logging.DEBUG if settings.app.debug else logging.INFO)


def get_logger_with_context(name: str, **context: Any) -> logging.LoggerAdapter:
    """
    Get logger with additional context.
    
    Args:
        name: Logger name.
        **context: Additional context to include in log records.
        
    Returns:
        LoggerAdapter: Logger with context.
    """
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, context)


class RequestContextFilter(logging.Filter):
    """
    Filter to add request context to log records.
    
    This filter can be used to automatically add request-specific
    information to all log records within a request context.
    """
    
    def __init__(self, request_id: str = None, user_id: str = None, tenant_id: str = None):
        """
        Initialize request context filter.
        
        Args:
            request_id: Request ID to add to log records.
            user_id: User ID to add to log records.
            tenant_id: Tenant ID to add to log records.
        """
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id
        self.tenant_id = tenant_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request context to log record.
        
        Args:
            record: Log record to modify.
            
        Returns:
            bool: Always True (don't filter out records).
        """
        if self.request_id:
            record.request_id = self.request_id
        if self.user_id:
            record.user_id = self.user_id
        if self.tenant_id:
            record.tenant_id = self.tenant_id
        
        return True


# Initialize logging when module is imported
setup_logging()