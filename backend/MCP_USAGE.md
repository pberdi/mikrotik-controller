# Uso del Servidor MCP - Controlador MikroTik

## ¿Qué es MCP?

MCP (Model Context Protocol) es un protocolo que permite a los modelos de IA acceder a herramientas y recursos externos de manera estandarizada. Este proyecto ahora puede funcionar tanto como:

1. **API REST tradicional** (FastAPI)
2. **Servidor MCP** (para integración con IA)

## Configuración Inicial

### 1. Instalar Dependencias MCP

```bash
cd backend
./setup_mcp.sh
```

### 2. Configurar Base de Datos

```bash
# Si no lo has hecho antes
python seed_database.py
```

## Uso como Servidor MCP

### Ejecutar el Servidor MCP

```bash
# Opción 1: Directamente
python mcp_server.py

# Opción 2: Como paquete instalado
uvx mikrotik-controller-mcp
```

### Configurar en Cliente MCP

Para usar con Kiro u otros clientes MCP, agregar a la configuración:

```json
{
  "mcpServers": {
    "mikrotik-controller": {
      "command": "python",
      "args": ["/ruta/al/backend/mcp_server.py"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost/mikrotik_controller"
      }
    }
  }
}
```

## Herramientas Disponibles

### 1. Gestión de Dispositivos

#### `list_devices`
Lista todos los dispositivos MikroTik del tenant.

**Parámetros:**
- `tenant_id` (requerido): ID del tenant
- `page` (opcional): Número de página (default: 1)
- `page_size` (opcional): Elementos por página (default: 50)
- `status` (opcional): Filtrar por estado
- `online_only` (opcional): Solo dispositivos en línea

**Ejemplo:**
```json
{
  "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
  "page": 1,
  "page_size": 10,
  "online_only": true
}
```

#### `get_device`
Obtiene información detallada de un dispositivo específico.

**Parámetros:**
- `device_id` (requerido): ID del dispositivo
- `tenant_id` (requerido): ID del tenant

#### `create_device`
Crea un nuevo dispositivo MikroTik.

**Parámetros:**
- `tenant_id` (requerido): ID del tenant
- `user_id` (requerido): ID del usuario
- `name` (requerido): Nombre del dispositivo
- `host` (requerido): Dirección IP o hostname
- `username` (requerido): Usuario para conexión
- `password` (requerido): Contraseña para conexión
- `port` (opcional): Puerto de conexión (default: 8728)
- `description` (opcional): Descripción del dispositivo
- `site_id` (opcional): ID del sitio

#### `update_device`
Actualiza un dispositivo existente.

#### `delete_device`
Elimina un dispositivo.

#### `get_device_stats`
Obtiene estadísticas de dispositivos del tenant.

### 2. Gestión de Usuarios

#### `list_users`
Lista usuarios del sistema.

**Parámetros:**
- `tenant_id` (requerido): ID del tenant
- `user_id` (requerido): ID del usuario solicitante
- `page` (opcional): Número de página
- `page_size` (opcional): Elementos por página
- `is_active` (opcional): Filtrar por estado activo

### 3. Auditoría

#### `get_audit_logs`
Obtiene logs de auditoría del sistema.

**Parámetros:**
- `tenant_id` (requerido): ID del tenant
- `user_id` (requerido): ID del usuario
- `page` (opcional): Número de página
- `page_size` (opcional): Elementos por página
- `action` (opcional): Filtrar por acción
- `resource_type` (opcional): Filtrar por tipo de recurso
- `days` (opcional): Días hacia atrás (default: 7)

### 4. Alertas

#### `list_alerts`
Lista alertas del sistema.

**Parámetros:**
- `tenant_id` (requerido): ID del tenant
- `user_id` (requerido): ID del usuario
- `page` (opcional): Número de página
- `page_size` (opcional): Elementos por página
- `severity` (opcional): Filtrar por severidad
- `status` (opcional): Filtrar por estado

## Ejemplos de Uso

### Con Kiro

```
# Listar dispositivos
Usa la herramienta list_devices con tenant_id "123e4567-e89b-12d3-a456-426614174000"

# Crear dispositivo
Usa create_device para agregar un nuevo MikroTik con:
- tenant_id: "123e4567-e89b-12d3-a456-426614174000"
- user_id: "456e7890-e89b-12d3-a456-426614174000"
- name: "Router Principal"
- host: "192.168.1.1"
- username: "admin"
- password: "password123"

# Ver estadísticas
Usa get_device_stats para ver resumen de dispositivos
```

### Programáticamente

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_mikrotik_mcp():
    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Listar herramientas disponibles
            tools = await session.list_tools()
            print("Herramientas disponibles:", [tool.name for tool in tools.tools])
            
            # Usar herramienta
            result = await session.call_tool(
                "list_devices",
                {
                    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
                    "page": 1,
                    "page_size": 5
                }
            )
            print("Dispositivos:", result.content[0].text)

# Ejecutar
asyncio.run(use_mikrotik_mcp())
```

## Diferencias con API REST

| Aspecto | API REST | MCP Server |
|---------|----------|------------|
| **Protocolo** | HTTP/JSON | JSON-RPC/stdio |
| **Autenticación** | JWT Tokens | Context-based |
| **Uso** | Aplicaciones web/móviles | Integración con IA |
| **Formato** | Endpoints REST | Herramientas (tools) |
| **Estado** | Stateless | Session-based |

## Ventajas del MCP

1. **Integración con IA**: Los modelos pueden usar las herramientas directamente
2. **Protocolo Estándar**: Compatible con múltiples clientes MCP
3. **Contexto Persistente**: Mantiene contexto durante la sesión
4. **Tipado Fuerte**: Esquemas JSON para validación automática
5. **Bidireccional**: El servidor puede notificar al cliente

## Limitaciones Actuales

1. **Sin Autenticación JWT**: Usa context-based auth (tenant_id/user_id)
2. **Sin WebSocket**: Solo stdio por ahora
3. **Sin Streaming**: Respuestas completas únicamente
4. **Sin Notificaciones**: Solo request/response

## Próximos Pasos

1. **Agregar más herramientas**: Templates, Jobs, Backups
2. **Implementar WebSocket**: Para clientes web
3. **Agregar notificaciones**: Para eventos en tiempo real
4. **Mejorar autenticación**: Integrar con sistema JWT existente
5. **Agregar streaming**: Para operaciones largas

## Troubleshooting

### Error: "Module mcp not found"
```bash
pip install mcp>=1.0.0
```

### Error: "Database connection failed"
Verificar variables de entorno en `.env`:
```bash
DATABASE_URL=postgresql://user:pass@localhost/mikrotik_controller
```

### Error: "Permission denied"
Verificar que el usuario tenga permisos en el tenant especificado.

## Soporte

Para problemas específicos del MCP server, revisar logs:
```bash
python mcp_server.py 2>&1 | tee mcp_server.log
```