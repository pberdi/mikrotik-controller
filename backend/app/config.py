"""
Configuration management system using Pydantic BaseSettings.

This module provides environment-based configuration for the application
with validation and support for multiple deployment environments.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database connection configuration."""
    
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="mikrotik_controller", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: Optional[str] = Field(default=None, description="Database password")
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    echo: bool = Field(default=False, description="Echo SQL queries")
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        case_sensitive=False
    )
    
    @property
    def url(self) -> str:
        """Generate database URL."""
        if self.password:
            return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql+psycopg://{self.user}@{self.host}:{self.port}/{self.name}"


class RedisConfig(BaseSettings):
    """Redis connection configuration."""
    
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    max_connections: int = Field(default=50, description="Max connections in pool")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    socket_connect_timeout: int = Field(default=5, description="Socket connect timeout")
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        case_sensitive=False
    )
    
    @property
    def url(self) -> str:
        """Generate Redis URL."""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class SecurityConfig(BaseSettings):
    """Security and authentication configuration."""
    
    secret_key: str = Field(description="Secret key for JWT signing")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    password_min_length: int = Field(default=8, description="Minimum password length")
    encryption_key: str = Field(description="Master encryption key for credentials")
    
    model_config = SettingsConfigDict(
        env_prefix="SECURITY_",
        case_sensitive=False
    )
    
    @field_validator("secret_key", "encryption_key")
    @classmethod
    def validate_keys(cls, v: str) -> str:
        """Validate that security keys are sufficiently long."""
        if len(v) < 32:
            raise ValueError("Security keys must be at least 32 characters long")
        return v


class ApplicationConfig(BaseSettings):
    """General application configuration."""
    
    app_name: str = Field(default="MikroTik Controller", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_prefix: str = Field(default="/api/v1", description="API route prefix")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS allowed origins")
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute per user")
    
    # Pagination
    default_page_size: int = Field(default=50, description="Default pagination page size")
    max_page_size: int = Field(default=100, description="Maximum pagination page size")
    
    # Worker Configuration
    celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL (defaults to Redis)")
    celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend (defaults to Redis)")
    celery_task_time_limit: int = Field(default=300, description="Task time limit in seconds")
    celery_task_soft_time_limit: int = Field(default=270, description="Task soft time limit in seconds")
    
    # Health Check
    health_check_timeout: int = Field(default=1, description="Health check timeout in seconds")
    
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v_upper


class Settings(BaseSettings):
    """
    Main settings class that aggregates all configuration sections.
    
    This class loads configuration from environment variables and validates
    all required settings at application startup.
    """
    
    # Database fields with DB_ prefix
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="mikrotik_controller", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: Optional[str] = Field(default=None, description="Database password")
    db_pool_size: int = Field(default=20, description="Connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")
    db_echo: bool = Field(default=False, description="Echo SQL queries")
    
    # Redis fields with REDIS_ prefix
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_max_connections: int = Field(default=50, description="Max connections in pool")
    redis_socket_timeout: int = Field(default=5, description="Socket timeout in seconds")
    redis_socket_connect_timeout: int = Field(default=5, description="Socket connect timeout")
    
    # Security fields with SECURITY_ prefix
    security_secret_key: str = Field(description="Secret key for JWT signing")
    security_algorithm: str = Field(default="HS256", description="JWT algorithm")
    security_access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    security_refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")
    security_password_min_length: int = Field(default=8, description="Minimum password length")
    security_encryption_key: str = Field(description="Master encryption key for credentials")
    
    # Application fields with APP_ prefix
    app_name: str = Field(default="MikroTik Controller", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_environment: str = Field(default="development", description="Environment (development, staging, production)")
    app_debug: bool = Field(default=False, description="Debug mode")
    app_log_level: str = Field(default="INFO", description="Logging level")
    app_api_prefix: str = Field(default="/api/v1", description="API route prefix")
    app_cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS allowed origins")
    app_cors_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    app_cors_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    app_cors_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")
    app_rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    app_rate_limit_per_minute: int = Field(default=60, description="Requests per minute per user")
    app_default_page_size: int = Field(default=50, description="Default pagination page size")
    app_max_page_size: int = Field(default=100, description="Maximum pagination page size")
    app_celery_broker_url: Optional[str] = Field(default=None, description="Celery broker URL (defaults to Redis)")
    app_celery_result_backend: Optional[str] = Field(default=None, description="Celery result backend (defaults to Redis)")
    app_celery_task_time_limit: int = Field(default=300, description="Task time limit in seconds")
    app_celery_task_soft_time_limit: int = Field(default=270, description="Task soft time limit in seconds")
    app_health_check_timeout: int = Field(default=1, description="Health check timeout in seconds")
    
    # Nested config objects (computed fields)
    database: Optional[DatabaseConfig] = Field(default=None, exclude=True)
    redis: Optional[RedisConfig] = Field(default=None, exclude=True)
    security: Optional[SecurityConfig] = Field(default=None, exclude=True)
    app: Optional[ApplicationConfig] = Field(default=None, exclude=True)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("security_secret_key", "security_encryption_key")
    @classmethod
    def validate_keys(cls, v: str) -> str:
        """Validate that security keys are sufficiently long."""
        if len(v) < 32:
            raise ValueError("Security keys must be at least 32 characters long")
        return v
    
    @field_validator("app_environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @field_validator("app_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}")
        return v_upper
    
    def __init__(self, **kwargs):
        """Initialize settings and create nested config objects."""
        super().__init__(**kwargs)
        
        # Create nested config objects from the loaded values
        self.database = DatabaseConfig(
            host=self.db_host,
            port=self.db_port,
            name=self.db_name,
            user=self.db_user,
            password=self.db_password,
            pool_size=self.db_pool_size,
            max_overflow=self.db_max_overflow,
            pool_timeout=self.db_pool_timeout,
            echo=self.db_echo
        )
        
        self.redis = RedisConfig(
            host=self.redis_host,
            port=self.redis_port,
            db=self.redis_db,
            password=self.redis_password,
            max_connections=self.redis_max_connections,
            socket_timeout=self.redis_socket_timeout,
            socket_connect_timeout=self.redis_socket_connect_timeout
        )
        
        self.security = SecurityConfig(
            secret_key=self.security_secret_key,
            algorithm=self.security_algorithm,
            access_token_expire_minutes=self.security_access_token_expire_minutes,
            refresh_token_expire_days=self.security_refresh_token_expire_days,
            password_min_length=self.security_password_min_length,
            encryption_key=self.security_encryption_key
        )
        
        self.app = ApplicationConfig(
            app_name=self.app_name,
            app_version=self.app_version,
            environment=self.app_environment,
            debug=self.app_debug,
            log_level=self.app_log_level,
            api_prefix=self.app_api_prefix,
            cors_origins=self.app_cors_origins,
            cors_credentials=self.app_cors_credentials,
            cors_methods=self.app_cors_methods,
            cors_headers=self.app_cors_headers,
            rate_limit_enabled=self.app_rate_limit_enabled,
            rate_limit_per_minute=self.app_rate_limit_per_minute,
            default_page_size=self.app_default_page_size,
            max_page_size=self.app_max_page_size,
            celery_broker_url=self.app_celery_broker_url,
            celery_result_backend=self.app_celery_result_backend,
            celery_task_time_limit=self.app_celery_task_time_limit,
            celery_task_soft_time_limit=self.app_celery_task_soft_time_limit,
            health_check_timeout=self.app_health_check_timeout
        )
        
        # Set Celery URLs to Redis if not explicitly configured
        if not self.app.celery_broker_url:
            self.app.celery_broker_url = self.redis.url
        if not self.app.celery_result_backend:
            self.app.celery_result_backend = self.redis.url
    
    def validate_production_config(self) -> None:
        """
        Validate that production environment has secure configuration.
        
        Raises:
            ValueError: If production environment has insecure settings.
        """
        if self.app.environment == "production":
            if self.app.debug:
                raise ValueError("Debug mode must be disabled in production")
            if "localhost" in self.app.cors_origins:
                raise ValueError("CORS origins must not include localhost in production")
            if self.database.echo:
                raise ValueError("Database query echo must be disabled in production")
    
    def mask_sensitive_values(self) -> dict:
        """
        Return configuration dict with sensitive values masked.
        
        Returns:
            dict: Configuration with masked sensitive values.
        """
        config = self.model_dump()
        
        # Mask sensitive fields
        if "database" in config and "password" in config["database"]:
            config["database"]["password"] = "***MASKED***"
        if "redis" in config and "password" in config["redis"] and config["redis"]["password"]:
            config["redis"]["password"] = "***MASKED***"
        if "security" in config:
            config["security"]["secret_key"] = "***MASKED***"
            config["security"]["encryption_key"] = "***MASKED***"
        
        return config


# Global settings instance
settings = Settings()

# Validate production configuration
settings.validate_production_config()
