# Guía de Inicio Rápido - Controlador MikroTik

Esta guía te ayudará a configurar y ejecutar el backend del Controlador MikroTik en tu entorno de desarrollo local.

## 📋 Prerrequisitos

### Requisitos del Sistema
- **Sistema Operativo:** macOS, Linux, o Windows con WSL2
- **Python:** 3.11 o superior
- **PostgreSQL:** 15 o superior
- **Redis:** 7 o superior
- **Git:** Para clonar el repositorio

### Instalación en macOS
```bash
# Instalar dependencias usando Homebrew
brew install postgresql@15 redis python@3.11

# Iniciar servicios
brew services start postgresql@15
brew services start redis
```

### Instalación en Linux (Ubuntu/Debian)
```bash
# Actualizar paquetes
sudo apt update

# Instalar PostgreSQL
sudo apt install postgresql postgresql-contrib

# Instalar Redis
sudo apt install redis-server

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Iniciar servicios
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

## 🚀 Configuración Rápida (Automatizada)

La forma más fácil de comenzar es usando el script de configuración automatizada:

```bash
cd backend
chmod +x setup_dev.sh
./setup_dev.sh
```

Este script:
1. Crea un archivo `.env` con secretos generados
2. Configura un entorno virtual de Python
3. Instala todas las dependencias
4. Verifica conectividad a PostgreSQL y Redis
5. Crea la base de datos
6. Ejecuta las migraciones de base de datos
7. Valida la configuración

## 🛠️ Configuración Manual

Si prefieres configurar manualmente o el script automatizado no funciona:

### 1. Clonar el Repositorio
```bash
git clone <url-del-repositorio>
cd mikrotik-controller/backend
```

### 2. Configurar Entorno Virtual
```bash
# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate     # En Windows
```

### 3. Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip

# Instalar dependencias de producción
pip install -r requirements.txt

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Instalar dependencias adicionales necesarias
pip install "psycopg[binary]" email-validator
```

### 4. Configurar PostgreSQL

```bash
# Iniciar PostgreSQL (si no está ejecutándose)
# macOS:
brew services start postgresql

# Linux:
sudo systemctl start postgresql

# O usar Docker:
docker run -d --name postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  postgres:15
```

#### Crear Base de Datos
```bash
# Conectar a PostgreSQL (ajustar usuario según tu configuración)
psql -U postgres

# Crear base de datos
CREATE DATABASE mikrotik_controller;

# Crear usuario (opcional)
CREATE USER mikrotik_user WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE mikrotik_controller TO mikrotik_user;

# Salir de psql
\q
```

### 5. Configurar Redis

```bash
# Iniciar Redis (si no está ejecutándose)
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis

# O usar Docker:
docker run -d --name redis \
  -p 6379:6379 \
  redis:7
```

### 6. Configurar Variables de Entorno

El archivo `.env` ya está configurado con valores por defecto. Ajusta si es necesario:

```bash
# Revisar configuración actual
cat .env

# Editar si necesitas cambiar la configuración
nano .env
```

Variables importantes:
- `DB_USER`: Usuario de PostgreSQL (por defecto: pablo)
- `DB_PASSWORD`: Contraseña de BD (vacía por defecto)
- `DB_NAME`: Nombre de la base de datos (mikrotik_controller)
- `SECURITY_SECRET_KEY`: Clave secreta para JWT (ya configurada)
- `SECURITY_ENCRYPTION_KEY`: Clave de encriptación (ya configurada)

### 7. Ejecutar Migraciones
```bash
# Validar configuración
python validate_config.py

# Ejecutar migraciones de base de datos
alembic upgrade head
```

### 8. Sembrar Datos de Prueba
```bash
# Crear datos iniciales (roles, usuarios, dispositivos de prueba)
python seed_database.py
```

## 🏃‍♂️ Ejecutar el Servidor de Desarrollo

### Iniciar el Servidor API

```bash
# Activar entorno virtual (si no está activo)
source venv/bin/activate

# Iniciar servidor con auto-recarga
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en:
- **API Base:** http://localhost:8000
- **Documentación (Swagger):** http://localhost:8000/docs
- **Documentación (ReDoc):** http://localhost:8000/redoc
- **Especificación OpenAPI:** http://localhost:8000/openapi.json

### Probar la API

```bash
# En una nueva terminal, ejecutar el script de pruebas
python test_api.py
```

Esto verificará:
- Endpoints de health check
- Conectividad a la base de datos
- Conectividad a Redis
- Documentación de la API
- Configuración CORS

## 🔐 Credenciales de Prueba

El script de seeding crea los siguientes usuarios de prueba:

```
Administrador del Tenant:
  Email: admin@test.com
  Password: admin123
  Rol: TenantAdmin

Gerente de Sitio:
  Email: manager@test.com
  Password: manager123
  Rol: SiteManager

Operador:
  Email: operator@test.com
  Password: operator123
  Rol: Operator

Visualizador:
  Email: viewer@test.com
  Password: viewer123
  Rol: Viewer
```

## 🧪 Probar la API

### Usando la Documentación Interactiva
1. Ve a http://localhost:8000/docs
2. Haz clic en "Authorize"
3. Usa las credenciales de prueba para obtener un token
4. Prueba los diferentes endpoints

### Usando curl
```bash
# Obtener token de acceso
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin123"}'

# Usar el token para acceder a endpoints protegidos
curl -X GET "http://localhost:8000/api/v1/devices" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

## 🛠️ Comandos Útiles de Desarrollo

### Gestión de Base de Datos
```bash
# Ver estado actual de migraciones
alembic current

# Crear nueva migración
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1

# Ver historial de migraciones
alembic history
```

### Testing
```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=app --cov-report=html

# Ejecutar tests específicos
pytest tests/test_services/test_device_service.py

# Ejecutar con salida detallada
pytest -v

# Probar API manualmente
python test_api.py
```

### Calidad de Código
```bash
# Formatear código con black
black app tests

# Verificar estilo de código con flake8
flake8 app tests

# Verificación de tipos con mypy
mypy app
```

### Validación y Configuración
```bash
# Validar configuración
python validate_config.py

# Verificar conectividad a PostgreSQL
pg_isready -h localhost -p 5432

# Verificar conectividad a Redis
redis-cli ping
```

## 🔄 Flujo de Desarrollo Típico

1. **Activar entorno:** `source venv/bin/activate`
2. **Hacer cambios** en el código
3. **Ejecutar tests:** `pytest`
4. **Verificar calidad:** `black app && flake8 app`
5. **Probar manualmente** usando la documentación en http://localhost:8000/docs
6. **Crear migración** (si cambias modelos): `alembic revision --autogenerate -m "descripción"`
7. **Aplicar migración:** `alembic upgrade head`
8. **Validar configuración:** `python validate_config.py`

## 🐛 Solución de Problemas Comunes

### "No se puede conectar a la base de datos"
```bash
# Verificar que PostgreSQL esté ejecutándose
pg_isready -h localhost -p 5432

# Verificar configuración en .env
cat .env | grep DB_

# Probar conexión manual
psql -U pablo -h localhost -p 5432 -d mikrotik_controller
```

### "No se puede conectar a Redis"
```bash
# Verificar que Redis esté ejecutándose
redis-cli ping  # Debe devolver PONG

# Verificar configuración de Redis en .env
cat .env | grep REDIS_
```

### Errores de "Módulo no encontrado"
```bash
# Asegurar que el entorno virtual esté activado
source venv/bin/activate

# Reinstalar dependencias
pip install --force-reinstall -r requirements.txt
pip install "psycopg[binary]" email-validator
```

### "Alembic no puede encontrar modelos"
```bash
# Verificar que todos los modelos estén importados
cat app/models/__init__.py

# Verificar configuración de alembic
cat alembic/env.py | grep "from app.models"
```

### "Puerto 8000 ya está en uso"
```bash
# Encontrar y terminar el proceso
lsof -ti:8000 | xargs kill -9

# O usar un puerto diferente
uvicorn app.main:app --reload --port 8001
```

### Errores de JWT/Autenticación
```bash
# Verificar que las claves de seguridad estén configuradas
cat .env | grep SECURITY_

# Regenerar claves si es necesario
python3 -c "import secrets; print('SECURITY_SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('SECURITY_ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

## 📁 Archivos Importantes

```
backend/
├── .env                    # Variables de entorno
├── requirements.txt        # Dependencias de producción
├── requirements-dev.txt    # Dependencias de desarrollo
├── alembic.ini            # Configuración de migraciones
├── validate_config.py     # Script de validación
├── seed_database.py       # Script de datos de prueba
├── test_api.py           # Tests manuales de API
├── setup_dev.sh          # Script de configuración automatizada
├── app/
│   ├── main.py           # Punto de entrada de la aplicación
│   ├── config.py         # Configuración de la aplicación
│   ├── dependencies.py   # Dependencias de FastAPI
│   └── [otros módulos]
└── alembic/
    └── versions/          # Archivos de migración
```

## 🎯 Próximos Pasos

Una vez que la API esté ejecutándose:

1. **Explorar la documentación** en http://localhost:8000/docs
2. **Probar autenticación** usando el endpoint `/api/v1/auth/login`
3. **Probar gestión de dispositivos** con los endpoints de devices
4. **Revisar logs de auditoría** para ver todas las acciones rastreadas
5. **Continuar desarrollo** siguiendo las tareas en `.kiro/specs/backend-architecture/tasks.md`

## 📚 Recursos Útiles

- **Documentación FastAPI:** https://fastapi.tiangolo.com/
- **Documentación SQLAlchemy:** https://docs.sqlalchemy.org/
- **Documentación Alembic:** https://alembic.sqlalchemy.org/
- **Documentación Pydantic:** https://docs.pydantic.dev/
- **Estado del Proyecto:** `ESTADO_ACTUAL_PROYECTO.md`

## 📞 Obtener Ayuda

Si encuentras problemas:

1. **Revisa los logs** en la terminal donde se ejecuta el servidor
2. **Verifica la configuración** con `python validate_config.py`
3. **Revisa los logs de la base de datos**
4. **Asegúrate** de que todos los prerrequisitos estén instalados y ejecutándose
5. **Intenta el script automatizado** nuevamente: `./setup_dev.sh`
6. **Consulta la documentación** en `docs/specs/`
7. **Revisa el estado del proyecto** en `ESTADO_ACTUAL_PROYECTO.md`

---

**¡Listo!** Ahora tienes el backend del Controlador MikroTik ejecutándose en tu entorno de desarrollo.

Para continuar con el desarrollo, revisa las tareas pendientes en `.kiro/specs/backend-architecture/tasks.md`.