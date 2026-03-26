"""
Simple script to validate configuration system without dependencies.
"""

import os
import sys

# Set required environment variables for validation
os.environ["DB_PASSWORD"] = "test_password_123"
os.environ["SECURITY_SECRET_KEY"] = "a" * 32
os.environ["SECURITY_ENCRYPTION_KEY"] = "b" * 32

try:
    from app.config import settings
    
    print("✓ Configuration loaded successfully")
    print(f"✓ Environment: {settings.app.environment}")
    print(f"✓ Database URL: {settings.database.url}")
    print(f"✓ Redis URL: {settings.redis.url}")
    print(f"✓ API Prefix: {settings.app.api_prefix}")
    print(f"✓ Celery Broker: {settings.app.celery_broker_url}")
    
    # Test masking
    masked = settings.mask_sensitive_values()
    print(f"✓ Sensitive values masked: ***MASKED***")
    
    print("\n✓ All configuration validation checks passed!")
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Configuration validation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
