"""
Database connection and session management.

This module provides SQLAlchemy engine configuration, session management,
and FastAPI dependency injection for database operations.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from ..config import settings
from ..models.base import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager for handling SQLAlchemy engine and session lifecycle.
    
    This class provides centralized database configuration and session management
    with connection pooling, transaction handling, and error recovery.
    """
    
    def __init__(self):
        """Initialize database manager with engine and session factory."""
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None
        self._initialized = False
    
    def initialize(self) -> None:
        """
        Initialize database engine and session factory.
        
        This method should be called once during application startup.
        """
        if self._initialized:
            return
        
        # Create engine with connection pooling
        self._engine = create_engine(
            settings.database.url,
            # Connection pool configuration
            poolclass=QueuePool,
            pool_size=settings.database.pool_size,
            max_overflow=settings.database.max_overflow,
            pool_timeout=settings.database.pool_timeout,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            # Query configuration
            echo=settings.database.echo,
            echo_pool=settings.app.debug,
            # Connection configuration
            connect_args={
                "connect_timeout": 10,
                "application_name": settings.app.app_name,
            }
        )
        
        # Add connection event listeners
        self._setup_engine_events()
        
        # Create session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("Database manager initialized successfully")
    
    def _setup_engine_events(self) -> None:
        """Set up SQLAlchemy engine event listeners."""
        if not self._engine:
            return
        
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set database-specific connection parameters."""
            # This is primarily for PostgreSQL, but can be extended for other databases
            pass
        
        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log connection checkout for debugging."""
            if settings.app.debug:
                logger.debug("Connection checked out from pool")
        
        @event.listens_for(self._engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log connection checkin for debugging."""
            if settings.app.debug:
                logger.debug("Connection checked in to pool")
    
    @property
    def engine(self) -> Engine:
        """
        Get the SQLAlchemy engine.
        
        Returns:
            Engine: The SQLAlchemy engine instance.
            
        Raises:
            RuntimeError: If database manager is not initialized.
        """
        if not self._initialized or not self._engine:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker[Session]:
        """
        Get the session factory.
        
        Returns:
            sessionmaker: The SQLAlchemy session factory.
            
        Raises:
            RuntimeError: If database manager is not initialized.
        """
        if not self._initialized or not self._session_factory:
            raise RuntimeError("Database manager not initialized. Call initialize() first.")
        return self._session_factory
    
    def create_session(self) -> Session:
        """
        Create a new database session.
        
        Returns:
            Session: A new SQLAlchemy session instance.
        """
        return self.session_factory()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions with automatic cleanup.
        
        This context manager provides automatic transaction management:
        - Commits on successful completion
        - Rolls back on exceptions
        - Always closes the session
        
        Yields:
            Session: A database session with automatic transaction management.
            
        Example:
            with db_manager.get_session() as session:
                user = session.query(User).first()
                user.name = "Updated Name"
                # Automatic commit on success, rollback on exception
        """
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self) -> None:
        """
        Create all database tables.
        
        This method creates all tables defined in the Base metadata.
        Should only be used for development/testing.
        """
        if not self._engine:
            raise RuntimeError("Database manager not initialized")
        
        Base.metadata.create_all(bind=self._engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self) -> None:
        """
        Drop all database tables.
        
        This method drops all tables defined in the Base metadata.
        Should only be used for development/testing.
        """
        if not self._engine:
            raise RuntimeError("Database manager not initialized")
        
        Base.metadata.drop_all(bind=self._engine)
        logger.info("Database tables dropped successfully")
    
    def check_connection(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise.
        """
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def close(self) -> None:
        """
        Close database connections and clean up resources.
        
        This method should be called during application shutdown.
        """
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")
        
        self._engine = None
        self._session_factory = None
        self._initialized = False


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    
    This dependency provides automatic session lifecycle management for FastAPI endpoints:
    - Creates a new session for each request
    - Commits on successful completion
    - Rolls back on exceptions
    - Always closes the session
    
    Yields:
        Session: A database session with automatic transaction management.
        
    Example:
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
    """
    session = db_manager.create_session()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in request: {e}")
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error in request: {e}")
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Initialize database manager.
    
    This function should be called during application startup.
    """
    db_manager.initialize()


def close_db() -> None:
    """
    Close database connections.
    
    This function should be called during application shutdown.
    """
    db_manager.close()


# Health check function for monitoring
def check_db_health() -> dict[str, str]:
    """
    Check database health for monitoring endpoints.
    
    Returns:
        dict: Health status information.
    """
    try:
        is_healthy = db_manager.check_connection()
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "database": "connected" if is_healthy else "disconnected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }

def get_db_session():
    """
    Generator para obtener sesiones de base de datos para MCP.
    
    Yields:
        Session: Sesión de base de datos SQLAlchemy.
    """
    return get_db()