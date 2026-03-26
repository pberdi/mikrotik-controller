# Guía Completa de Deploy - Controlador MikroTik Sistema Híbrido

**Versión:** 1.0.0  
**Fecha:** 26 de Marzo, 2026  
**Sistema:** API REST + MCP Server + LLM Local

## 📋 Resumen del Sistema

El Controlador MikroTik es un sistema híbrido que combina:

- **API REST completa** - Gestión tradicional de dispositivos MikroTik
- **Servidor MCP integrado** - 9 herramientas para integración con IA
- **LLM local (Ollama)** - Procesamiento de lenguaje natural
- **Asistente inteligente** - Combina LLM + herramientas automáticamente

## 🖥️ Requerimientos del Servidor

### Hardware Mínimo
- **CPU:** 4 cores (recomendado: 8 cores)
- **RAM:** 8 GB (recomendado: 16 GB)
- **Almacenamiento:** 50 GB SSD
- **Red:** Conexión estable a internet para descarga inicial

### Hardware Recomendado para LLM
- **CPU:** Apple Silicon M1/M2 o Intel/AMD con AVX2
- **RAM:** 16 GB (recomendado: 32 GB)
- **GPU:** Opcional pero recomendado (Metal en macOS, CUDA en Linux)

### Sistemas Operativos Soportados
- **macOS:** 12.0+ (Monterey o superior)
- **Linux:** Ubuntu 20.04+, CentOS 8+, Debian 11+
- **Windows:** 10/11 (con WSL2 recomendado)

## 🔧 Instalación Paso a Paso

### Paso 1: Preparar el Sistema Base

#### En macOS:
```bash
# Instalar Homebrew si no está instalado
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependencias del sistema
brew install python@3.11 postgresql redis git
brew services start postgresql
brew services start redis
```

#### En Ubuntu/Debian:
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
                    postgresql postgresql-contrib redis-server \
                    git curl build-essential

# Iniciar servicios
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

#### En CentOS/RHEL:
```bash
# Instalar EPEL
sudo dnf install -y epel-release

# Instalar dependencias
sudo dnf install -y python3.11 python3.11-devel postgresql-server \
                    postgresql-contrib redis git curl gcc

# Inicializar PostgreSQL
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl start redis
sudo systemctl enable postgresql
sudo systemctl enable redis
```

### Paso 2: Configurar Base de Datos

```bash
# Conectar a PostgreSQL
sudo -u postgres psql

# Crear base de datos y usuario
CREATE DATABASE mikrotik_controller;
CREATE USER mikrotik_user WITH PASSWORD 'tu_password_seguro';
GRANT ALL PRIVILEGES ON DATABASE mikrotik_controller TO mikrotik_user;
\q
```

### Paso 3: Clonar y Configurar el Proyecto

```bash
# Clonar repositorio
git clone <tu-repositorio-url>
cd mikrotik-controller/backend

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements-hybrid.txt
```

### Paso 4: Configurar Variables de Entorno

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar configuración
nano .env
```

**Configuración mínima requerida:**
```env
# Base de datos
DATABASE_URL=postgresql+psycopg://mikrotik_user:tu_password_seguro@localhost:5432/mikrotik_controller

# Redis
REDIS_URL=redis://localhost:6379/0

# Seguridad
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_aqui
ENCRYPTION_KEY=otra_clave_de_32_caracteres_exactos

# Aplicación
APP_NAME=MikroTik Controller
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Paso 5: Instalar y Configurar Ollama

#### En macOS:
```bash
# Instalar Ollama
brew install ollama

# Iniciar servicio
brew services start ollama

# Descargar modelo recomendado
ollama pull llama3.2:3b
```

#### En Linux:
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar servicio
sudo systemctl start ollama
sudo systemctl enable ollama

# Descargar modelo
ollama pull llama3.2:3b
```

### Paso 6: Inicializar Base de Datos

```bash
# Aplicar migraciones
alembic upgrade head

# Sembrar datos de prueba
python seed_database.py
```

### Paso 7: Configuración Automática (Recomendado)

```bash
# Ejecutar script de configuración automática
chmod +x setup_hybrid.sh
./setup_hybrid.sh
```

**O configuración manual:**

```bash
# Verificar configuración
python validate_config.py

# Probar conexiones
python -c "
from app.core.database import get_db
from llm_integration import LLMManager
import asyncio

# Probar BD
db = next(get_db())
print('✅ Base de datos conectada')
db.close()

# Probar LLM
async def test_llm():
    llm = LLMManager()
    await llm.initialize()
    print('✅ LLM inicializado')
    await llm.cleanup()

asyncio.run(test_llm())
"
```

## 🚀 Iniciar el Sistema

### Modo Desarrollo
```bash
# Activar entorno virtual
source venv/bin/activate

# Iniciar sistema híbrido
PYTHONPATH=. python -m app.main_hybrid
```

### Modo Producción

#### Usando Gunicorn (Recomendado)
```bash
# Instalar Gunicorn
pip install gunicorn

# Crear archivo de configuración
cat > gunicorn.conf.py << EOF
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5
preload_app = True
EOF

# Iniciar con Gunicorn
gunicorn app.main_hybrid:app -c gunicorn.conf.py
```

#### Usando Systemd (Linux)
```bash
# Crear archivo de servicio
sudo tee /etc/systemd/system/mikrotik-controller.service << EOF
[Unit]
Description=MikroTik Controller Hybrid System
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=tu_usuario
Group=tu_grupo
WorkingDirectory=/ruta/a/tu/proyecto/backend
Environment=PATH=/ruta/a/tu/proyecto/backend/venv/bin
Environment=PYTHONPATH=/ruta/a/tu/proyecto/backend
ExecStart=/ruta/a/tu/proyecto/backend/venv/bin/gunicorn app.main_hybrid:app -c gunicorn.conf.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Habilitar e iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable mikrotik-controller
sudo systemctl start mikrotik-controller
```

## 🔒 Configuración de Seguridad

### Firewall
```bash
# Ubuntu/Debian
sudo ufw allow 8000/tcp
sudo ufw allow 5432/tcp  # Solo si BD está en otro servidor
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

### SSL/TLS (Recomendado para Producción)

#### Usando Nginx como Proxy Reverso
```bash
# Instalar Nginx
sudo apt install nginx  # Ubuntu/Debian
sudo dnf install nginx  # CentOS/RHEL

# Configurar sitio
sudo tee /etc/nginx/sites-available/mikrotik-controller << EOF
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tu-dominio.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/mikrotik-controller /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 📊 Monitoreo y Logs

### Logs del Sistema
```bash
# Ver logs en tiempo real
tail -f /var/log/mikrotik-controller/app.log

# Logs de systemd
sudo journalctl -u mikrotik-controller -f

# Logs de Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Monitoreo de Salud
```bash
# Endpoint de salud
curl http://localhost:8000/api/health

# Estado del sistema híbrido
curl http://localhost:8000/hybrid/capabilities

# Estado del LLM
curl http://localhost:8000/llm/status
```

## 🧪 Verificación del Deploy

### Script de Pruebas Automáticas
```bash
# Ejecutar pruebas completas
python test_hybrid.py

# Pruebas específicas
curl -X POST http://localhost:8000/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "get_device_stats",
    "arguments": {
      "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "550e8400-e29b-41d4-a716-446655440001"
    }
  }'
```

### Credenciales de Prueba
```
Admin:    admin@test.com / admin123
Manager:  manager@test.com / manager123
Operator: operator@test.com / operator123
Viewer:   viewer@test.com / viewer123
```

## 🔧 Mantenimiento

### Backup de Base de Datos
```bash
# Crear backup
pg_dump -U mikrotik_user -h localhost mikrotik_controller > backup_$(date +%Y%m%d_%H%M%S).sql

# Restaurar backup
psql -U mikrotik_user -h localhost mikrotik_controller < backup_file.sql
```

### Actualización del Sistema
```bash
# Detener servicio
sudo systemctl stop mikrotik-controller

# Actualizar código
git pull origin main

# Actualizar dependencias
source venv/bin/activate
pip install -r requirements-hybrid.txt

# Aplicar migraciones
alembic upgrade head

# Reiniciar servicio
sudo systemctl start mikrotik-controller
```

### Limpieza de Logs
```bash
# Rotar logs automáticamente
sudo tee /etc/logrotate.d/mikrotik-controller << EOF
/var/log/mikrotik-controller/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 tu_usuario tu_grupo
    postrotate
        systemctl reload mikrotik-controller
    endscript
}
EOF
```

## 🚨 Solución de Problemas

### Problemas Comunes

#### 1. Error de Conexión a Base de Datos
```bash
# Verificar estado de PostgreSQL
sudo systemctl status postgresql

# Verificar conexión
psql -U mikrotik_user -h localhost -d mikrotik_controller -c "SELECT 1;"
```

#### 2. Ollama No Responde
```bash
# Verificar estado de Ollama
curl http://localhost:11434/api/tags

# Reiniciar Ollama
sudo systemctl restart ollama

# Verificar logs
sudo journalctl -u ollama -f
```

#### 3. Error de Permisos
```bash
# Verificar propietario de archivos
sudo chown -R tu_usuario:tu_grupo /ruta/al/proyecto

# Verificar permisos de ejecución
chmod +x setup_hybrid.sh
```

#### 4. Puerto en Uso
```bash
# Verificar qué proceso usa el puerto
sudo lsof -i :8000

# Cambiar puerto en configuración
export PORT=8001
```

## 📞 Soporte

### Información del Sistema
```bash
# Generar reporte de estado
python -c "
import sys
import platform
import psutil
from app.config import settings

print(f'Sistema: {platform.system()} {platform.release()}')
print(f'Python: {sys.version}')
print(f'CPU: {psutil.cpu_count()} cores')
print(f'RAM: {psutil.virtual_memory().total // (1024**3)} GB')
print(f'Configuración: {settings.app.app_name} v{settings.app.app_version}')
"
```

### Logs de Debug
```bash
# Habilitar debug en .env
DEBUG=true
LOG_LEVEL=DEBUG

# Reiniciar servicio
sudo systemctl restart mikrotik-controller
```

---

**¡Deploy completado!** 🎉

Tu sistema híbrido MikroTik Controller está listo para usar:
- **API REST:** http://tu-servidor:8000/api/*
- **Documentación:** http://tu-servidor:8000/docs
- **Asistente IA:** http://tu-servidor:8000/hybrid/assistant

Para soporte adicional, consulta los logs del sistema y la documentación técnica.