#!/usr/bin/env python3
"""
Script de validación de integridad del código.

Este script verifica la sintaxis, imports y lógica básica de todos los módulos
principales del proyecto para detectar errores potenciales.
"""

import sys
import traceback
from pathlib import Path

def test_imports():
    """Prueba que todos los módulos principales se importen correctamente."""
    modules_to_test = [
        'app.main',
        'app.config',
        'app.core.database',
        'app.core.security',
        'app.core.middleware',
        'app.dependencies',
        'app.models.user',
        'app.models.device',
        'app.schemas.user',
        'app.schemas.device',
        'app.services.base_service',
        'app.services.user_service',
        'app.services.device_service',
        'app.services.audit_service',
        'app.services.alert_service',
        'app.api.v1.auth',
        'app.api.v1.devices',
    ]
    
    failed_imports = []
    
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            failed_imports.append((module, str(e)))
    
    return failed_imports

def test_app_creation():
    """Prueba que la aplicación FastAPI se pueda crear correctamente."""
    try:
        from app.main import create_app
        app = create_app()
        print("✓ Aplicación FastAPI creada correctamente")
        return True
    except Exception as e:
        print(f"✗ Error creando aplicación FastAPI: {e}")
        traceback.print_exc()
        return False

def test_database_models():
    """Prueba que los modelos de base de datos se puedan importar."""
    try:
        from app.models import User, Device, Tenant, Role, Permission
        print("✓ Modelos de base de datos importados correctamente")
        return True
    except Exception as e:
        print(f"✗ Error importando modelos: {e}")
        return False

def test_services():
    """Prueba que los servicios se puedan instanciar."""
    try:
        from sqlalchemy.orm import Session
        from app.services.user_service import UserService
        from app.services.device_service import DeviceService
        from app.services.audit_service import AuditService
        
        # Mock session para pruebas
        class MockSession:
            def query(self, *args):
                return self
            def filter(self, *args):
                return self
            def first(self):
                return None
            def add(self, *args):
                pass
            def flush(self):
                pass
            def commit(self):
                pass
            def rollback(self):
                pass
        
        mock_db = MockSession()
        
        # Probar instanciación de servicios
        user_service = UserService(db=mock_db, tenant_id="test", user_id="test")
        device_service = DeviceService(db=mock_db, tenant_id="test", user_id="test")
        audit_service = AuditService(db=mock_db, tenant_id="test", user_id="test")
        
        print("✓ Servicios instanciados correctamente")
        return True
    except Exception as e:
        print(f"✗ Error instanciando servicios: {e}")
        traceback.print_exc()
        return False

def main():
    """Función principal de validación."""
    print("=== Validación de Integridad del Código ===\n")
    
    print("1. Probando imports de módulos...")
    failed_imports = test_imports()
    
    print("\n2. Probando creación de aplicación...")
    app_ok = test_app_creation()
    
    print("\n3. Probando modelos de base de datos...")
    models_ok = test_database_models()
    
    print("\n4. Probando servicios...")
    services_ok = test_services()
    
    print("\n=== Resumen ===")
    
    if failed_imports:
        print(f"✗ {len(failed_imports)} módulos fallaron al importar:")
        for module, error in failed_imports:
            print(f"  - {module}: {error}")
    else:
        print("✓ Todos los módulos se importaron correctamente")
    
    if app_ok:
        print("✓ Aplicación FastAPI funcional")
    else:
        print("✗ Problemas con la aplicación FastAPI")
    
    if models_ok:
        print("✓ Modelos de base de datos funcionales")
    else:
        print("✗ Problemas con modelos de base de datos")
    
    if services_ok:
        print("✓ Servicios funcionales")
    else:
        print("✗ Problemas con servicios")
    
    # Determinar resultado final
    all_ok = not failed_imports and app_ok and models_ok and services_ok
    
    if all_ok:
        print("\n🎉 ¡Validación exitosa! El código está libre de errores básicos.")
        return 0
    else:
        print("\n❌ Se encontraron problemas. Revisar los errores arriba.")
        return 1

if __name__ == "__main__":
    sys.exit(main())