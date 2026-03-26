# MikroTik Controller - Backend Sistema Híbrido

Backend con **Sistema Híbrido** que combina API REST tradicional + Servidor MCP + LLM Local para gestión inteligente de dispositivos MikroTik.

## 🚀 Características Únicas

### 🤖 **Sistema Híbrido Innovador**
- **API REST completa** para gestión tradicional
- **Servidor MCP** con 9 herramientas para IA
- **LLM local** (Ollama + llama3.2:3b) sin dependencias externas
- **Asistente inteligente** que combina todo automáticamente

### 🎯 **Primera Implementación**
Este es el **primer backend MikroTik con IA integrada**, revolucionando la gestión de redes con capacidades de lenguaje natural.

## 🏗️ Arquitectura del Sistema Híbrido

```
┌─────────────────────────────────────────────────────────────┐
│                 BACKEND HÍBRIDO                             │
│                 Puerto 8000                                 │
├─────────────────────────────────────────────────────────────┤
│  🌐 API REST (COMPLETA)                                    │
│  • FastAPI con autenticación JWT                           │
│  • PostgreSQL con aislamiento multi-tenant                 │
│  • Redis para cache y sesiones                             │
├─────────────────────────────────────────────────────────────┤
│  🔧 MCP SERVER                                            │
│  • 9 herramientas especializadas                           │
│  • Integración directa con servicios                       │
│  • Ejecución segura con permisos de usuario                │
├─────────────────────────────────────────────────────────────┤
│  🤖 LLM LOCAL                                             │
│  • Ollama con modelo llama3.2:3b (2GB)                     │
│  • Procesamiento local privado                             │
│  • Expertise específico en MikroTik RouterOS               │
├─────────────────────────────────────────────────────────────┤
│  🧠 ASISTENTE HÍBRIDO                                     │
│  • Combina LLM + herramientas MCP automáticamente          │
│  • Chat en tiempo real con streaming                       │
│  • Ejecución de operaciones por lenguaje natural           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
backend/
├── app/
│   ├── main.py              # 🌐 API REST tradicional
│   ├── main_hybrid.py       # 🆕 Sistema híbrido principal
│   ├── api/v1/              # Endpoints REST API
│   │   ├── auth.py         # ✅ Autenticación JWT
│   │   └── devices.py      # ✅ Gestión de dispositivos
│   ├── models/             # 12 modelos SQLAlchemy
│   ├── schemas/            # Esquemas Pydantic
│   ├── services/           # 8 servicios de negocio
│   ├── core/               # Seguridad, BD, middleware
│   └── utils/              # Utilidades y encriptación
├── llm_integration.py      # 🆕 Integración LLM local
├── mcp_server.py          # 🆕 Servidor MCP standalone
├── setup_hybrid.sh        # 🆕 Configuración automática
├── test_hybrid.py         # 🆕 Pruebas del sistema
├── requirements-hybrid.txt # 🆕 Dependencias híbridas
├── alembic/               # Migraciones de BD
└── tests/                 # Suite de pruebas
```

## 🚀 Inicio Rápido

### Opción 1: Configuración Automática (Recomendada)

```bash
# Configuración automática del sistema híbrido
./setup_hybrid.sh
```

**Esto configura automáticamente:**
- ✅ Entorno Python y dependencias híbridas
- ✅ PostgreSQL y Redis
- ✅ Ollama y modelo LLM (llama3.2:3b)
- ✅ Base de datos con migraciones y datos de prueba
- ✅ Verificación completa del sistema

### Opción 2: Configuración Manual

```bash
# Prerrequisitos
brew install postgresql redis python@3.11 ollama

# Configurar entorno
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements-hybrid.txt

# Configurar LLM local
ollama serve
ollama pull llama3.2:3b

# Configurar base de datos
createdb mikrotik_controller
alembic upgrade head
python seed_database.py

# Iniciar sistema híbrido
python -m app.main_hybrid
```

## 🎯 Modos de Operación

### 1. Sistema Híbrido (Recomendado)
```bash
python -m app.main_hybrid
```
**Incluye:** API REST + MCP Server + LLM Local + Asistente Híbrido

### 2. API REST Tradicional
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
**Incluye:** Solo API REST tradicional

### 3. Servidor MCP Standalone
```bash
python mcp_server.py
```
**Incluye:** Solo servidor MCP para integración externa

## 🌐 Endpoints Disponibles

### Sistema Híbrido (`/`)
- `GET /` - Información del sistema híbrido
- `GET /hybrid/capabilities` - Capacidades disponibles

### MCP Server (`/mcp`)
- `GET /mcp/tools` - Lista de herramientas MCP
- `POST /mcp/call-tool` - Ejecutar herramientas

### LLM Local (`/llm`)
- `GET /llm/status` - Estado del LLM
- `POST /llm/chat` - Chat directo
- `POST /llm/chat/stream` - Chat con streaming

### Asistente Híbrido (`/hybrid`)
- `POST /hybrid/assistant` - Asistente inteligente
- `POST /hybrid/assistant/stream` - Con streaming

### API REST Tradicional (`/api/v1`)
- `POST /api/v1/auth/login` - Autenticación
- `GET /api/v1/devices` - Gestión de dispositivos
- `GET /api/v1/health` - Health checks

## 🤖 Herramientas MCP Disponibles

1. **list_devices** - Lista dispositivos MikroTik con filtros
2. **get_device** - Información detallada de dispositivos
3. **create_device** - Crear y adoptar nuevos dispositivos
4. **update_device** - Actualizar configuraciones
5. **delete_device** - Eliminar dispositivos del sistema
6. **get_device_stats** - Estadísticas y métricas
7. **list_users** - Lista usuarios del sistema
8. **get_audit_logs** - Acceso a logs de auditoría
9. **list_alerts** - Sistema de alertas

## 🧪 Testing y Validación

### Pruebas Automáticas del Sistema Híbrido
```bash
# Ejecutar suite completa de pruebas
python test_hybrid.py

# Resultados esperados: 7/8 pruebas exitosas (87.5%)
```

### Pruebas Individuales
```bash
# Probar API REST
curl http://localhost:8000/api/v1/health

# Probar MCP Server
curl http://localhost:8000/mcp/tools

# Probar LLM Local
curl -X POST http://localhost:8000/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola"}'

# Probar Asistente Híbrido
curl -X POST http://localhost:8000/hybrid/assistant \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuántos dispositivos tengo?",
    "tenant_id": "test-tenant",
    "user_id": "test-user"
  }'
```

### Pruebas Tradicionales
```bash
# Ejecutar tests unitarios
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests específicos
pytest tests/test_services/
```

## 🔧 Configuración

### Variables de Entorno Principales
```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@localhost/mikrotik_controller

# Redis
REDIS_URL=redis://localhost:6379

# Seguridad
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256

# IA Local
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Entorno
ENVIRONMENT=development
```

### Archivos de Configuración
- `.env` - Variables de entorno
- `requirements-hybrid.txt` - Dependencias del sistema híbrido
- `requirements.txt` - Dependencias básicas
- `alembic.ini` - Configuración de migraciones

## 🔐 Seguridad y Privacidad

### Características de Seguridad
- **IA Local:** Todo el procesamiento de IA es local, sin envío de datos externos
- **Multi-Tenant:** Aislamiento completo de datos por organización
- **JWT Tokens:** Autenticación segura con refresh tokens
- **Encriptación:** AES-256 para credenciales de dispositivos
- **RBAC:** Control de acceso basado en roles
- **Auditoría:** Log completo de todas las operaciones

### Aislamiento de IA
- **Conversaciones por tenant:** Cada organización tiene conversaciones aisladas
- **Permisos de usuario:** IA respeta los permisos del usuario autenticado
- **Datos privados:** Ningún dato se envía a servicios externos

## 📊 Monitoreo y Observabilidad

### Health Checks
- `/health` - Estado general del sistema
- `/health/database` - Conectividad de base de datos
- `/health/redis` - Estado de Redis
- `/llm/status` - Estado del LLM local
- `/hybrid/capabilities` - Capacidades del sistema híbrido

### Métricas y Logs
- **Prometheus:** Métricas de aplicación en `/metrics`
- **Structured Logging:** Logs JSON con correlación de requests
- **Performance:** Tracking de tiempo de respuesta de IA
- **Audit Trail:** Log completo de operaciones de IA

## 🛠️ Desarrollo

### Configuración del Entorno de Desarrollo
```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Configurar pre-commit hooks
pre-commit install

# Ejecutar linters
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

### Migraciones de Base de Datos
```bash
# Crear nueva migración
alembic revision --autogenerate -m "Descripción de cambios"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Desarrollo de Nuevas Herramientas MCP
```python
# Ejemplo de nueva herramienta MCP
@server.tool("nueva_herramienta")
async def nueva_herramienta(parametro: str):
    """Descripción de la nueva herramienta"""
    # Implementación
    return resultado
```

## 📖 Documentación

### Documentación Principal
- **[Sistema Híbrido](SISTEMA_HIBRIDO_RESUMEN.md)** - Guía completa del sistema híbrido
- **[Uso Híbrido](HYBRID_USAGE.md)** - Cómo usar todas las características
- **[MCP Usage](MCP_USAGE.md)** - Uso específico del servidor MCP
- **[Guía de Deploy](GUIA_DEPLOY.md)** - Despliegue en producción

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Spec:** http://localhost:8000/openapi.json

## 🚀 Despliegue

### Docker Compose (Recomendado)
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mikrotik_controller
      - REDIS_URL=redis://redis:6379
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - db
      - redis
      - ollama

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
```

### Producción
Ver **[GUIA_DEPLOY.md](GUIA_DEPLOY.md)** para instrucciones completas de despliegue en producción.

## 🎯 Ventajas del Backend Híbrido

1. **🤖 IA Integrada:** Primera implementación con IA nativa
2. **🔒 Privacidad Total:** LLM local, sin dependencias externas
3. **🧠 Lenguaje Natural:** API tradicional + chat inteligente
4. **🔧 Arquitectura Modular:** Componentes independientes y escalables
5. **📈 Alto Rendimiento:** Optimizado para 1000+ dispositivos
6. **🛡️ Seguridad Avanzada:** Multi-tenant con aislamiento completo
7. **⚡ Tiempo Real:** Streaming de respuestas y actualizaciones
8. **🌐 Multi-idioma:** Soporte nativo español e inglés

## 🤝 Contribución

### Cómo Contribuir
1. **Fork** el repositorio
2. **Crear** rama para nueva característica
3. **Implementar** siguiendo los estándares del proyecto
4. **Probar** con `python test_hybrid.py`
5. **Documentar** los cambios
6. **Pull Request** con descripción detallada

### Estándares de Código
- **Python:** PEP 8, type hints, docstrings
- **Commits:** Conventional commits
- **Testing:** Cobertura mínima 80%
- **Documentación:** Actualizar con cambios

---

**🎉 ¡El futuro de los backends MikroTik está aquí!**

**Última Actualización:** 26 de Marzo, 2026  
**Versión:** 1.0.0-hybrid  
**Estado:** 🟢 Sistema Híbrido Operativo