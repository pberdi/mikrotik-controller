"""
Core application components.

This package contains core functionality like database management,
security, middleware, and other foundational components.
"""

from .database import db_manager, get_db, init_db, close_db, check_db_health

__all__ = [
    "db_manager",
    "get_db", 
    "init_db",
    "close_db",
    "check_db_health",
]