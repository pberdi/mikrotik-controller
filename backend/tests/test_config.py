"""
Tests for configuration management system.
"""

import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError
from app.config import (
    DatabaseConfig,
    RedisConfig,
    SecurityConfig,
    ApplicationConfig,
    Settings,
)


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = DatabaseConfig(password="test_password")
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "mikrotik_controller"
        assert config.pool_size == 20
    
    def test_database_url_generation(self):
        """Test database URL generation."""
        config = DatabaseConfig(
            host="db.example.com",
            port=5433,
            name="testdb",
            user="testuser",
            password="testpass"
        )
        expected_url = "postgresql://testuser:testpass@db.example.com:5433/testdb"
        assert config.url == expected_url


class TestRedisConfig:
    """Test Redis configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = RedisConfig()
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
    
    def test_redis_url_without_password(self):
        """Test Redis URL generation without password."""
        config = RedisConfig(host="redis.example.com", port=6380, db=1)
        expected_url = "redis://redis.example.com:6380/1"
        assert config.url == expected_url
    
    def test_redis_url_with_password(self):
        """Test Redis URL generation with password."""
        config = RedisConfig(
            host="redis.example.com",
            password="secret"
        )
        expected_url = "redis://:secret@redis.example.com:6379/0"
        assert config.url == expected_url


class TestSecurityConfig:
    """Test security configuration."""
    
    def test_valid_security_keys(self):
        """Test valid security key configuration."""
        config = SecurityConfig(
            secret_key="a" * 32,
            encryption_key="b" * 32
        )
        assert len(config.secret_key) == 32
        assert len(config.encryption_key) == 32
    
    def test_short_secret_key_raises_error(self):
        """Test that short secret keys are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(
                secret_key="short",
                encryption_key="b" * 32
            )
        assert "at least 32 characters" in str(exc_info.value)
    
    def test_short_encryption_key_raises_error(self):
        """Test that short encryption keys are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SecurityConfig(
                secret_key="a" * 32,
                encryption_key="short"
            )
        assert "at least 32 characters" in str(exc_info.value)


class TestApplicationConfig:
    """Test application configuration."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ApplicationConfig()
        assert config.app_name == "MikroTik Controller"
        assert config.environment == "development"
        assert config.api_prefix == "/api/v1"
        assert config.default_page_size == 50
        assert config.max_page_size == 100
    
    def test_valid_environment(self):
        """Test valid environment values."""
        for env in ["development", "staging", "production"]:
            config = ApplicationConfig(environment=env)
            assert config.environment == env
    
    def test_invalid_environment_raises_error(self):
        """Test that invalid environment values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationConfig(environment="invalid")
        assert "Environment must be one of" in str(exc_info.value)
    
    def test_valid_log_level(self):
        """Test valid log level values."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            config = ApplicationConfig(log_level=level)
            assert config.log_level == level
    
    def test_log_level_case_insensitive(self):
        """Test that log level is case insensitive."""
        config = ApplicationConfig(log_level="info")
        assert config.log_level == "INFO"
    
    def test_invalid_log_level_raises_error(self):
        """Test that invalid log levels are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ApplicationConfig(log_level="INVALID")
        assert "Log level must be one of" in str(exc_info.value)


class TestSettings:
    """Test main settings class."""
    
    def test_settings_initialization(self, monkeypatch):
        """Test settings initialization with environment variables."""
        # Set required environment variables
        monkeypatch.setenv("DB_PASSWORD", "test_db_pass")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SECURITY_ENCRYPTION_KEY", "b" * 32)
        
        settings = Settings()
        assert settings.database.password == "test_db_pass"
        assert settings.security.secret_key == "a" * 32
        assert settings.security.encryption_key == "b" * 32
    
    def test_celery_urls_default_to_redis(self, monkeypatch):
        """Test that Celery URLs default to Redis URL."""
        monkeypatch.setenv("DB_PASSWORD", "test_db_pass")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SECURITY_ENCRYPTION_KEY", "b" * 32)
        
        settings = Settings()
        assert settings.app.celery_broker_url == settings.redis.url
        assert settings.app.celery_result_backend == settings.redis.url
    
    def test_production_validation_rejects_debug_mode(self, monkeypatch):
        """Test that production environment rejects debug mode."""
        monkeypatch.setenv("DB_PASSWORD", "test_db_pass")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SECURITY_ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        monkeypatch.setenv("APP_DEBUG", "true")
        
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "Debug mode must be disabled in production" in str(exc_info.value)
    
    def test_production_validation_rejects_localhost_cors(self, monkeypatch):
        """Test that production environment rejects localhost in CORS."""
        monkeypatch.setenv("DB_PASSWORD", "test_db_pass")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SECURITY_ENCRYPTION_KEY", "b" * 32)
        monkeypatch.setenv("APP_ENVIRONMENT", "production")
        monkeypatch.setenv("APP_CORS_ORIGINS", '["http://localhost:3000"]')
        
        with pytest.raises(ValueError) as exc_info:
            Settings()
        assert "CORS origins must not include localhost in production" in str(exc_info.value)
    
    def test_mask_sensitive_values(self, monkeypatch):
        """Test that sensitive values are masked in output."""
        monkeypatch.setenv("DB_PASSWORD", "secret_password")
        monkeypatch.setenv("REDIS_PASSWORD", "redis_secret")
        monkeypatch.setenv("SECURITY_SECRET_KEY", "a" * 32)
        monkeypatch.setenv("SECURITY_ENCRYPTION_KEY", "b" * 32)
        
        settings = Settings()
        masked = settings.mask_sensitive_values()
        
        assert masked["database"]["password"] == "***MASKED***"
        assert masked["redis"]["password"] == "***MASKED***"
        assert masked["security"]["secret_key"] == "***MASKED***"
        assert masked["security"]["encryption_key"] == "***MASKED***"
        
        # Verify non-sensitive values are not masked
        assert masked["database"]["host"] == "localhost"
        assert masked["redis"]["host"] == "localhost"



# ============================================================================
# Property-Based Tests
# ============================================================================

class TestConfigurationLoadingProperty:
    """
    Property-based tests for configuration loading.
    
    **Validates: Requirements 1.2, 7.1, 7.2**
    """
    
    @given(
        db_host=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        db_port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
        db_password=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    )
    def test_property_configuration_loading_from_environment(
        self, monkeypatch, db_host, db_port, db_password
    ):
        """
        **Property 1: Configuration Loading from Environment**
        
        For any configuration key defined in the system, loading configuration
        from environment variables should either:
        - Return the environment variable value if set
        - Return the default value if defined and env var not set
        - Raise an error if required and missing
        
        **Validates: Requirements 1.2, 7.1, 7.2**
        """
        # Clear any existing environment variables
        monkeypatch.delenv("DB_HOST", raising=False)
        monkeypatch.delenv("DB_PORT", raising=False)
        monkeypatch.delenv("DB_PASSWORD", raising=False)
        
        # Set environment variables if provided
        if db_host is not None:
            monkeypatch.setenv("DB_HOST", db_host)
        if db_port is not None:
            monkeypatch.setenv("DB_PORT", str(db_port))
        if db_password is not None:
            monkeypatch.setenv("DB_PASSWORD", db_password)
        
        # Test configuration loading behavior
        if db_password is None:
            # Required field missing - should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                DatabaseConfig()
            # Verify error message indicates missing required field
            assert "password" in str(exc_info.value).lower()
        else:
            # Required field present - should load successfully
            config = DatabaseConfig()
            
            # Verify environment variable values are used when set
            if db_host is not None:
                assert config.host == db_host
            else:
                # Verify default value is used when env var not set
                assert config.host == "localhost"
            
            if db_port is not None:
                assert config.port == db_port
            else:
                # Verify default value is used when env var not set
                assert config.port == 5432
            
            # Verify required field value is loaded from environment
            assert config.password == db_password
    
    @given(
        redis_host=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
        redis_port=st.one_of(st.none(), st.integers(min_value=1, max_value=65535)),
        redis_password=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    )
    def test_property_redis_configuration_loading(
        self, monkeypatch, redis_host, redis_port, redis_password
    ):
        """
        Test configuration loading for Redis config (all fields optional).
        
        **Validates: Requirements 1.2, 7.1, 7.2**
        """
        # Clear any existing environment variables
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)
        monkeypatch.delenv("REDIS_PASSWORD", raising=False)
        
        # Set environment variables if provided
        if redis_host is not None:
            monkeypatch.setenv("REDIS_HOST", redis_host)
        if redis_port is not None:
            monkeypatch.setenv("REDIS_PORT", str(redis_port))
        if redis_password is not None:
            monkeypatch.setenv("REDIS_PASSWORD", redis_password)
        
        # All Redis fields have defaults, so loading should always succeed
        config = RedisConfig()
        
        # Verify environment variable values are used when set
        if redis_host is not None:
            assert config.host == redis_host
        else:
            # Verify default value is used when env var not set
            assert config.host == "localhost"
        
        if redis_port is not None:
            assert config.port == redis_port
        else:
            # Verify default value is used when env var not set
            assert config.port == 6379
        
        if redis_password is not None:
            assert config.password == redis_password
        else:
            # Verify default value (None) is used when env var not set
            assert config.password is None
    
    @given(
        secret_key=st.one_of(st.none(), st.text(min_size=32, max_size=100)),
        encryption_key=st.one_of(st.none(), st.text(min_size=32, max_size=100)),
        algorithm=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
    )
    def test_property_security_configuration_with_validation(
        self, monkeypatch, secret_key, encryption_key, algorithm
    ):
        """
        Test configuration loading with field validation for security config.
        
        **Validates: Requirements 1.2, 7.1, 7.2, 7.3**
        """
        # Clear any existing environment variables
        monkeypatch.delenv("SECURITY_SECRET_KEY", raising=False)
        monkeypatch.delenv("SECURITY_ENCRYPTION_KEY", raising=False)
        monkeypatch.delenv("SECURITY_ALGORITHM", raising=False)
        
        # Set environment variables if provided
        if secret_key is not None:
            monkeypatch.setenv("SECURITY_SECRET_KEY", secret_key)
        if encryption_key is not None:
            monkeypatch.setenv("SECURITY_ENCRYPTION_KEY", encryption_key)
        if algorithm is not None:
            monkeypatch.setenv("SECURITY_ALGORITHM", algorithm)
        
        # Test configuration loading behavior
        if secret_key is None or encryption_key is None:
            # Required fields missing - should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                SecurityConfig()
            error_str = str(exc_info.value).lower()
            # Verify error message indicates missing required field(s)
            if secret_key is None:
                assert "secret_key" in error_str
            if encryption_key is None:
                assert "encryption_key" in error_str
        else:
            # Required fields present - should load successfully
            config = SecurityConfig()
            
            # Verify required field values are loaded from environment
            assert config.secret_key == secret_key
            assert config.encryption_key == encryption_key
            
            # Verify environment variable or default value is used for optional field
            if algorithm is not None:
                assert config.algorithm == algorithm
            else:
                # Verify default value is used when env var not set
                assert config.algorithm == "HS256"
    
    @given(
        environment=st.one_of(
            st.none(),
            st.sampled_from(["development", "staging", "production"]),
            st.text(min_size=1, max_size=20).filter(
                lambda x: x not in ["development", "staging", "production"]
            )
        ),
        log_level=st.one_of(
            st.none(),
            st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
            st.text(min_size=1, max_size=20).filter(
                lambda x: x.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            )
        ),
    )
    def test_property_application_configuration_with_enum_validation(
        self, monkeypatch, environment, log_level
    ):
        """
        Test configuration loading with enum validation for application config.
        
        **Validates: Requirements 1.2, 7.1, 7.2, 7.3**
        """
        # Clear any existing environment variables
        monkeypatch.delenv("APP_ENVIRONMENT", raising=False)
        monkeypatch.delenv("APP_LOG_LEVEL", raising=False)
        
        # Set environment variables if provided
        if environment is not None:
            monkeypatch.setenv("APP_ENVIRONMENT", environment)
        if log_level is not None:
            monkeypatch.setenv("APP_LOG_LEVEL", log_level)
        
        # Determine if validation should fail
        valid_environments = ["development", "staging", "production"]
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        env_invalid = environment is not None and environment not in valid_environments
        log_invalid = log_level is not None and log_level.upper() not in valid_log_levels
        
        if env_invalid or log_invalid:
            # Invalid enum value - should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                ApplicationConfig()
            error_str = str(exc_info.value)
            # Verify error message indicates validation failure
            if env_invalid:
                assert "Environment must be one of" in error_str
            if log_invalid:
                assert "Log level must be one of" in error_str
        else:
            # Valid or default values - should load successfully
            config = ApplicationConfig()
            
            # Verify environment variable or default value is used
            if environment is not None:
                assert config.environment == environment
            else:
                # Verify default value is used when env var not set
                assert config.environment == "development"
            
            # Verify environment variable or default value is used for log level
            if log_level is not None:
                assert config.log_level == log_level.upper()
            else:
                # Verify default value is used when env var not set
                assert config.log_level == "INFO"
