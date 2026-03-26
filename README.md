# Controlador MikroTik - Plataforma SaaS Multi-Tenant

Una plataforma completa de gestión para dispositivos MikroTik RouterOS, diseñada como SaaS multi-tenant escalable.

## 🎯 Descripción del Proyecto

Este proyecto implementa un controlador centralizado para gestionar dispositivos MikroTik RouterOS en entornos empresariales. La plataforma permite la administración remota, configuración automatizada, respaldos programados y monitoreo de hasta 10,000+ routers MikroTik.

### Características Principales

- **Multi-Tenant:** Aislamiento completo entre organizaciones
- **Escalable:** Soporta de 500 a 10,000+ dispositivos MikroTik
- **Seguro:** Autenticación JWT, RBAC, encriptación de credenciales
- **Automatizado:** Plantillas de configuración, respaldos automáticos
- **Monitoreo:** Alertas en tiempo real, auditoría completa
- **API REST:** Documentación OpenAPI completa

## 📁 Estructura del Proyecto

```
mikrotik-controller/
├── docs/specs/              # 📋 Especificaciones técnicas (fuente de verdad)
├── backend/                 # 🔧 Backend FastAPI + PostgreSQL
│   ├── app/                 # Aplicación principal
│   ├── alembic/            # Migraciones de base de datos
│   ├── tests/              # Tests automatizados
│   └── venv/               # Entorno virtual Python
├── frontend/               # 🎨 Frontend (pendiente)
├── ai/                     # 🤖 Prompts para herramientas de IA
└── ESTADO_ACTUAL_PROYECTO.md # 📊 Estado actual detallado
```

## 🚀 Estado Actual

**Progreso General:** ~40% completado  
**Estado:** 🟡 En desarrollo activo

### ✅ Completado
- Arquitectura base y modelos de datos
- Sistema de autenticación JWT + RBAC
- APIs de autenticación y gestión de dispositivos
- Base de datos PostgreSQL con migraciones
- Capa de servicios completa
- Middleware multi-tenant
- Encriptación de credenciales

### 🔄 En Progreso
- Validación completa del servidor API
- Tests automatizados

### ⏳ Pendiente
- APIs restantes (templates, jobs, backups, alerts, users)
- Workers Celery para tareas asíncronas
- Conectores MikroTik RouterOS
- Motores de plantillas y respaldos
- Frontend web

## 🛠️ Tecnologías Utilizadas

### Backend
- **Framework:** FastAPI 0.109.0
- **Base de Datos:** PostgreSQL + SQLAlchemy 2.0
- **Cache:** Redis
- **Autenticación:** JWT (python-jose)
- **Validación:** Pydantic v2
- **Migraciones:** Alembic
- **Tareas Asíncronas:** Celery (pendiente)
- **Testing:** pytest + hypothesis

### Infraestructura
- **Contenedores:** Docker + docker-compose
- **Monitoreo:** Prometheus + métricas personalizadas
- **Logs:** Structured logging con JSON
- **Seguridad:** HTTPS, CORS, headers de seguridad

## 🏃‍♂️ Inicio Rápido

### Prerrequisitos
```bash
# macOS
brew install postgresql redis python@3.11

# Iniciar servicios
brew services start postgresql
brew services start redis
```

### Configuración del Backend
```bash
# Clonar repositorio
git clone <repo-url>
cd mikrotik-controller/backend

# Configurar entorno
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurar base de datos
createdb mikrotik_controller
alembic upgrade head
python seed_database.py

# Validar configuración
python validate_config.py

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceso a la Aplicación
- **API:** http://localhost:8000
- **Documentación:** http://localhost:8000/docs
- **OpenAPI Spec:** http://localhost:8000/openapi.json

### Credenciales de Prueba
```
Administrador: admin@test.com / admin123
Gerente:       manager@test.com / manager123
Operador:      operator@test.com / operator123
Visualizador:  viewer@test.com / viewer123
```

## 📖 Documentación

- **[Estado Actual](ESTADO_ACTUAL_PROYECTO.md)** - Progreso detallado del proyecto
- **[Especificaciones](docs/specs/)** - Documentación técnica completa
- **[Guía de Desarrollo](backend/QUICKSTART.md)** - Setup del entorno de desarrollo
- **[Testing](backend/TESTING.md)** - Guía de testing y calidad

## 🏗️ Arquitectura

### Componentes Principales

1. **API Gateway** - FastAPI con autenticación JWT
2. **Base de Datos** - PostgreSQL con modelos multi-tenant
3. **Cache** - Redis para sesiones y cache
4. **Workers** - Celery para tareas asíncronas (pendiente)
5. **Conectores** - Integración con RouterOS API (pendiente)
6. **Motores** - Plantillas, respaldos, alertas (pendiente)

### Flujo de Datos
```
Cliente → API Gateway → Middleware → Servicios → Base de Datos
                    ↓
                Workers → MikroTik Devices
```

## 🔐 Seguridad

- **Autenticación:** JWT con refresh tokens
- **Autorización:** RBAC con 5 roles predefinidos
- **Multi-Tenancy:** Aislamiento completo de datos
- **Encriptación:** AES-256 para credenciales de dispositivos
- **Auditoría:** Log completo de todas las operaciones
- **Headers:** Configuración de seguridad HTTP

## 🧪 Testing

```bash
# Ejecutar tests
cd backend
source venv/bin/activate
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Tests de integración
python test_api.py
```

## 📊 Métricas y Monitoreo

- **Métricas:** Prometheus integrado
- **Logs:** Structured logging con correlación de requests
- **Health Checks:** Endpoints de salud para K8s/Docker
- **Performance:** Tracking de tiempo de respuesta

## 🤝 Contribución

### Flujo de Trabajo Recomendado

1. Leer las especificaciones en `docs/specs/`
2. Usar las specs como fuente de verdad
3. Implementar módulos siguiendo la arquitectura definida
4. Escribir tests para nueva funcionalidad
5. Actualizar documentación

### Estándares de Código
- **Python:** PEP 8, type hints, docstrings
- **Commits:** Conventional commits
- **Testing:** Cobertura mínima 80%
- **Documentación:** Actualizar con cambios

## 📅 Roadmap

### Fase 1 - MVP (6-8 semanas)
- [ ] Completar APIs restantes
- [ ] Implementar workers Celery
- [ ] Conector MikroTik básico
- [ ] Testing completo

### Fase 2 - Producción (4-6 semanas)
- [ ] Frontend web
- [ ] Deployment automatizado
- [ ] Monitoreo avanzado
- [ ] Documentación de usuario

### Fase 3 - Escalabilidad (4-6 semanas)
- [ ] Optimizaciones de performance
- [ ] Clustering y HA
- [ ] Métricas avanzadas
- [ ] Integraciones adicionales

## 📞 Soporte

Para preguntas, problemas o contribuciones:

- **Documentación:** Ver `docs/specs/` para detalles técnicos
- **Estado:** Revisar `ESTADO_ACTUAL_PROYECTO.md` para progreso actual
- **Issues:** Usar el sistema de issues del repositorio

---

**Última Actualización:** 25 de Marzo, 2026  
**Versión:** 1.0.0-dev  
**Licencia:** [Especificar licencia]
