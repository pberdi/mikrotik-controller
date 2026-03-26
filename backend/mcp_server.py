#!/usr/bin/env python3
"""
MCP Server para Controlador MikroTik

Este servidor MCP expone las funcionalidades del controlador MikroTik
como herramientas que pueden ser utilizadas por clientes MCP.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    TextContent,
    Tool,
    INVALID_PARAMS,
    INTERNAL_ERROR
)

# Importar servicios del controlador
from app.core.database import get_db
from app.services.device_service import DeviceService
from app.services.user_service import UserService
from app.services.audit_service import AuditService
from app.services.alert_service import AlertService
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

# Crear servidor MCP
server = Server("mikrotik-controller")

# Herramientas disponibles
TOOLS = [
    Tool(
        name="list_devices",
        description="Lista todos los dispositivos MikroTik",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "page": {"type": "integer", "default": 1, "description": "Número de página"},
                "page_size": {"type": "integer", "default": 50, "description": "Elementos por página"},
                "status": {"type": "string", "description": "Filtrar por estado"},
                "online_only": {"type": "boolean", "description": "Solo dispositivos en línea"}
            },
            "required": ["tenant_id"]
        }
    ),
    Tool(
        name="get_device",
        description="Obtiene información detallada de un dispositivo",
        inputSchema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "ID del dispositivo"},
                "tenant_id": {"type": "string", "description": "ID del tenant"}
            },
            "required": ["device_id", "tenant_id"]
        }
    ),
    Tool(
        name="create_device",
        description="Crea un nuevo dispositivo MikroTik",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario"},
                "name": {"type": "string", "description": "Nombre del dispositivo"},
                "host": {"type": "string", "description": "Dirección IP o hostname"},
                "username": {"type": "string", "description": "Usuario para conexión"},
                "password": {"type": "string", "description": "Contraseña para conexión"},
                "port": {"type": "integer", "default": 8728, "description": "Puerto de conexión"},
                "description": {"type": "string", "description": "Descripción del dispositivo"},
                "site_id": {"type": "string", "description": "ID del sitio (opcional)"}
            },
            "required": ["tenant_id", "user_id", "name", "host", "username", "password"]
        }
    ),
    Tool(
        name="update_device",
        description="Actualiza un dispositivo existente",
        inputSchema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "ID del dispositivo"},
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario"},
                "name": {"type": "string", "description": "Nuevo nombre"},
                "description": {"type": "string", "description": "Nueva descripción"},
                "site_id": {"type": "string", "description": "Nuevo ID del sitio"}
            },
            "required": ["device_id", "tenant_id", "user_id"]
        }
    ),
    Tool(
        name="delete_device",
        description="Elimina un dispositivo",
        inputSchema={
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "ID del dispositivo"},
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario"}
            },
            "required": ["device_id", "tenant_id", "user_id"]
        }
    ),
    Tool(
        name="get_device_stats",
        description="Obtiene estadísticas de dispositivos",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario"}
            },
            "required": ["tenant_id", "user_id"]
        }
    ),
    Tool(
        name="list_users",
        description="Lista usuarios del sistema",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario solicitante"},
                "page": {"type": "integer", "default": 1, "description": "Número de página"},
                "page_size": {"type": "integer", "default": 50, "description": "Elementos por página"},
                "is_active": {"type": "boolean", "description": "Filtrar por estado activo"}
            },
            "required": ["tenant_id", "user_id"]
        }
    ),
    Tool(
        name="get_audit_logs",
        description="Obtiene logs de auditoría",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario"},
                "page": {"type": "integer", "default": 1, "description": "Número de página"},
                "page_size": {"type": "integer", "default": 50, "description": "Elementos por página"},
                "action": {"type": "string", "description": "Filtrar por acción"},
                "resource_type": {"type": "string", "description": "Filtrar por tipo de recurso"},
                "days": {"type": "integer", "default": 7, "description": "Días hacia atrás"}
            },
            "required": ["tenant_id", "user_id"]
        }
    ),
    Tool(
        name="list_alerts",
        description="Lista alertas del sistema",
        inputSchema={
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "ID del tenant"},
                "user_id": {"type": "string", "description": "ID del usuario"},
                "page": {"type": "integer", "default": 1, "description": "Número de página"},
                "page_size": {"type": "integer", "default": 50, "description": "Elementos por página"},
                "severity": {"type": "string", "description": "Filtrar por severidad"},
                "status": {"type": "string", "description": "Filtrar por estado"}
            },
            "required": ["tenant_id", "user_id"]
        }
    )
]

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """Lista todas las herramientas disponibles."""
    return TOOLS

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja las llamadas a herramientas."""
    db = None
    try:
        # Obtener sesión de base de datos
        db_gen = get_db()
        db = next(db_gen)
        
        if name == "list_devices":
            return await handle_list_devices(db, arguments)
        elif name == "get_device":
            return await handle_get_device(db, arguments)
        elif name == "create_device":
            return await handle_create_device(db, arguments)
        elif name == "update_device":
            return await handle_update_device(db, arguments)
        elif name == "delete_device":
            return await handle_delete_device(db, arguments)
        elif name == "get_device_stats":
            return await handle_get_device_stats(db, arguments)
        elif name == "list_users":
            return await handle_list_users(db, arguments)
        elif name == "get_audit_logs":
            return await handle_get_audit_logs(db, arguments)
        elif name == "list_alerts":
            return await handle_list_alerts(db, arguments)
        else:
            raise ValueError(f"Herramienta desconocida: {name}")
            
    except Exception as e:
        logger.error(f"Error ejecutando herramienta {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    finally:
        if db:
            db.close()

async def handle_list_devices(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta list_devices."""
    tenant_id = arguments.get("tenant_id")
    page = arguments.get("page", 1)
    page_size = arguments.get("page_size", 50)
    status = arguments.get("status")
    online_only = arguments.get("online_only")
    
    device_service = DeviceService(db=db, tenant_id=tenant_id)
    
    # Crear filtros
    filters = {}
    if status:
        filters["status"] = status
    if online_only is not None:
        filters["online_only"] = online_only
    
    result = device_service.list_devices(
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    # Formatear respuesta
    devices_info = []
    for device in result["items"]:
        devices_info.append({
            "id": str(device.id),
            "name": device.name,
            "host": device.host,
            "status": device.status.value if device.status else None,
            "model": device.model,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "created_at": device.created_at.isoformat()
        })
    
    response = {
        "devices": devices_info,
        "pagination": {
            "page": result["page"],
            "page_size": result["page_size"],
            "total_count": result["total_count"],
            "total_pages": result["total_pages"]
        }
    }
    
    return [TextContent(type="text", text=json.dumps(response, indent=2))]

async def handle_get_device(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta get_device."""
    device_id = arguments.get("device_id")
    tenant_id = arguments.get("tenant_id")
    
    device_service = DeviceService(db=db, tenant_id=tenant_id)
    device = device_service.get_device(device_id)
    
    if not device:
        return [TextContent(type="text", text=f"Dispositivo {device_id} no encontrado")]
    
    device_info = {
        "id": str(device.id),
        "name": device.name,
        "host": device.host,
        "port": device.port,
        "status": device.status.value if device.status else None,
        "model": device.model,
        "version": device.version,
        "description": device.description,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "created_at": device.created_at.isoformat(),
        "updated_at": device.updated_at.isoformat(),
        "site_id": str(device.site_id) if device.site_id else None,
        "tenant_id": str(device.tenant_id)
    }
    
    return [TextContent(type="text", text=json.dumps(device_info, indent=2))]

async def handle_create_device(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta create_device."""
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    
    device_service = DeviceService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    # Crear objeto DeviceCreate
    device_data = DeviceCreate(
        name=arguments["name"],
        host=arguments["host"],
        username=arguments["username"],
        password=arguments["password"],
        port=arguments.get("port", 8728),
        description=arguments.get("description"),
        site_id=arguments.get("site_id")
    )
    
    device = device_service.create_device(device_data)
    db.commit()
    
    device_info = {
        "id": str(device.id),
        "name": device.name,
        "host": device.host,
        "status": device.status.value,
        "created_at": device.created_at.isoformat(),
        "message": "Dispositivo creado exitosamente"
    }
    
    return [TextContent(type="text", text=json.dumps(device_info, indent=2))]

async def handle_update_device(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta update_device."""
    device_id = arguments.get("device_id")
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    
    device_service = DeviceService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    # Crear objeto DeviceUpdate con solo los campos proporcionados
    update_data = {}
    if "name" in arguments:
        update_data["name"] = arguments["name"]
    if "description" in arguments:
        update_data["description"] = arguments["description"]
    if "site_id" in arguments:
        update_data["site_id"] = arguments["site_id"]
    
    device_update = DeviceUpdate(**update_data)
    device = device_service.update_device(device_id, device_update)
    
    if not device:
        return [TextContent(type="text", text=f"Dispositivo {device_id} no encontrado")]
    
    db.commit()
    
    device_info = {
        "id": str(device.id),
        "name": device.name,
        "description": device.description,
        "updated_at": device.updated_at.isoformat(),
        "message": "Dispositivo actualizado exitosamente"
    }
    
    return [TextContent(type="text", text=json.dumps(device_info, indent=2))]

async def handle_delete_device(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta delete_device."""
    device_id = arguments.get("device_id")
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    
    device_service = DeviceService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    deleted = device_service.delete_device(device_id)
    
    if not deleted:
        return [TextContent(type="text", text=f"Dispositivo {device_id} no encontrado")]
    
    db.commit()
    
    response = {
        "device_id": device_id,
        "message": "Dispositivo eliminado exitosamente"
    }
    
    return [TextContent(type="text", text=json.dumps(response, indent=2))]

async def handle_get_device_stats(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta get_device_stats."""
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    
    device_service = DeviceService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    stats = device_service.get_device_stats()
    
    return [TextContent(type="text", text=json.dumps(stats, indent=2))]

async def handle_list_users(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta list_users."""
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    page = arguments.get("page", 1)
    page_size = arguments.get("page_size", 50)
    is_active = arguments.get("is_active")
    
    user_service = UserService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    filters = {}
    if is_active is not None:
        filters["is_active"] = is_active
    
    result = user_service.list_users(
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    users_info = []
    for user in result["items"]:
        users_info.append({
            "id": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "role": user.role.name if user.role else None,
            "created_at": user.created_at.isoformat()
        })
    
    response = {
        "users": users_info,
        "pagination": {
            "page": result["page"],
            "page_size": result["page_size"],
            "total_count": result["total_count"],
            "total_pages": result["total_pages"]
        }
    }
    
    return [TextContent(type="text", text=json.dumps(response, indent=2))]

async def handle_get_audit_logs(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta get_audit_logs."""
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    page = arguments.get("page", 1)
    page_size = arguments.get("page_size", 50)
    action = arguments.get("action")
    resource_type = arguments.get("resource_type")
    
    audit_service = AuditService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    result = audit_service.list_audit_logs(
        action=action,
        resource_type=resource_type,
        page=page,
        page_size=page_size
    )
    
    logs_info = []
    for log in result["items"]:
        logs_info.append({
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "result": log.result,
            "timestamp": log.timestamp.isoformat(),
            "user_id": str(log.user_id) if log.user_id else None,
            "ip_address": log.ip_address
        })
    
    response = {
        "audit_logs": logs_info,
        "pagination": {
            "page": result["page"],
            "page_size": result["page_size"],
            "total_count": result["total_count"],
            "total_pages": result["total_pages"]
        }
    }
    
    return [TextContent(type="text", text=json.dumps(response, indent=2))]

async def handle_list_alerts(db, arguments: Dict[str, Any]) -> List[TextContent]:
    """Maneja la herramienta list_alerts."""
    tenant_id = arguments.get("tenant_id")
    user_id = arguments.get("user_id")
    page = arguments.get("page", 1)
    page_size = arguments.get("page_size", 50)
    severity = arguments.get("severity")
    status = arguments.get("status")
    
    alert_service = AlertService(
        db=db, 
        tenant_id=tenant_id, 
        user_id=user_id
    )
    
    filters = {}
    if severity:
        filters["severity"] = severity
    if status:
        filters["status"] = status
    
    result = alert_service.list_alerts(
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    alerts_info = []
    for alert in result["items"]:
        alerts_info.append({
            "id": str(alert.id),
            "title": alert.title,
            "message": alert.message,
            "severity": alert.severity.value if alert.severity else None,
            "status": alert.status.value if alert.status else None,
            "device_id": str(alert.device_id) if alert.device_id else None,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        })
    
    response = {
        "alerts": alerts_info,
        "pagination": {
            "page": result["page"],
            "page_size": result["page_size"],
            "total_count": result["total_count"],
            "total_pages": result["total_pages"]
        }
    }
    
    return [TextContent(type="text", text=json.dumps(response, indent=2))]

async def main():
    """Función principal del servidor MCP."""
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Iniciando servidor MCP para Controlador MikroTik")
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mikrotik-controller",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())