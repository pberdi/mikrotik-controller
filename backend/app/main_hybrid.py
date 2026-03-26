"""
Aplicación híbrida FastAPI + MCP Server + LLM Local

Esta aplicación combina:
1. API REST completa (sin cambios)
2. Servidor MCP integrado
3. LLM local para procesamiento de lenguaje natural
4. Endpoint de chat para interacción con LLM
"""

import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# Importar la aplicación FastAPI existente
from .main import create_app as create_rest_app
from .config import settings

# Importar componentes MCP
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server import server as mcp_server, handle_call_tool
from llm_integration import LLMManager, ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

# Modelos para endpoints de chat
class ChatMessage(BaseModel):
    message: str
    tenant_id: str
    user_id: str
    context: Optional[Dict[str, Any]] = None

class ChatStreamResponse(BaseModel):
    response: str
    tool_calls: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None

# Manager global para LLM
llm_manager: Optional[LLMManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan manager para la aplicación híbrida.
    """
    global llm_manager
    
    # Startup
    logger.info("Iniciando aplicación híbrida: API REST + MCP + LLM")
    
    # Inicializar base de datos
    from app.core.database import db_manager
    db_manager.initialize()
    logger.info("Base de datos inicializada")
    
    # Inicializar LLM local
    try:
        llm_manager = LLMManager()
        await llm_manager.initialize()
        logger.info("LLM local inicializado correctamente")
    except Exception as e:
        logger.error(f"Error inicializando LLM: {e}")
        llm_manager = None
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación híbrida")
    if llm_manager:
        await llm_manager.cleanup()
    db_manager.close()
    logger.info("Base de datos cerrada")

def create_hybrid_app() -> FastAPI:
    """
    Crear aplicación híbrida que combina API REST + MCP + LLM.
    
    Returns:
        FastAPI: Aplicación híbrida configurada.
    """
    # Crear aplicación base con API REST completa
    rest_app = create_rest_app()
    
    # Crear nueva aplicación híbrida
    app = FastAPI(
        title=f"{settings.app.app_name} - Híbrido",
        version=settings.app.app_version,
        description="API REST + MCP Server + LLM Local para Controlador MikroTik",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Montar la aplicación REST completa
    app.mount("/api", rest_app)
    
    # Agregar endpoints específicos para MCP y LLM
    add_mcp_endpoints(app)
    add_llm_endpoints(app)
    add_hybrid_endpoints(app)
    
    return app

def add_mcp_endpoints(app: FastAPI):
    """Agregar endpoints MCP a la aplicación."""
    
    @app.get("/mcp/tools")
    async def list_mcp_tools():
        """Lista todas las herramientas MCP disponibles."""
        # Importar las herramientas directamente desde mcp_server
        from mcp_server import TOOLS
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                for tool in TOOLS
            ]
        }
    
    @app.post("/mcp/call-tool")
    async def call_mcp_tool(request: Dict[str, Any]):
        """Ejecuta una herramienta MCP específica."""
        try:
            tool_name = request.get("tool_name")
            arguments = request.get("arguments", {})
            
            if not tool_name:
                raise HTTPException(status_code=400, detail="tool_name is required")
            
            result = await handle_call_tool(tool_name, arguments)
            return {
                "success": True,
                "result": result[0].text if result else None
            }
        except Exception as e:
            logger.error(f"Error ejecutando herramienta MCP {tool_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

def add_llm_endpoints(app: FastAPI):
    """Agregar endpoints para LLM local."""
    
    @app.get("/llm/status")
    async def llm_status():
        """Estado del LLM local."""
        if not llm_manager:
            return {"status": "not_initialized", "model": None}
        
        return {
            "status": "ready" if llm_manager.is_ready() else "loading",
            "model": llm_manager.model_name,
            "capabilities": llm_manager.get_capabilities()
        }
    
    @app.post("/llm/chat")
    async def chat_with_llm(chat_request: ChatMessage):
        """Chat directo con LLM local."""
        if not llm_manager or not llm_manager.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="LLM no disponible"
            )
        
        try:
            response = await llm_manager.chat(
                message=chat_request.message,
                context=chat_request.context
            )
            
            return ChatStreamResponse(
                response=response.content,
                metadata=response.metadata
            )
        except Exception as e:
            logger.error(f"Error en chat con LLM: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/llm/chat/stream")
    async def chat_stream_with_llm(chat_request: ChatMessage):
        """Chat con streaming del LLM local."""
        if not llm_manager or not llm_manager.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="LLM no disponible"
            )
        
        async def generate_stream():
            try:
                async for chunk in llm_manager.chat_stream(
                    message=chat_request.message,
                    context=chat_request.context
                ):
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            except Exception as e:
                logger.error(f"Error en streaming: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )

def add_hybrid_endpoints(app: FastAPI):
    """Agregar endpoints híbridos que combinan LLM + MCP."""
    
    @app.post("/hybrid/assistant")
    async def mikrotik_assistant(chat_request: ChatMessage):
        """
        Asistente inteligente para MikroTik que combina LLM + herramientas MCP.
        
        El LLM puede usar herramientas MCP automáticamente para responder consultas.
        """
        if not llm_manager or not llm_manager.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Asistente no disponible"
            )
        
        try:
            # Preparar contexto con herramientas MCP disponibles
            from mcp_server import TOOLS
            
            # Usar LLM con capacidades de herramientas
            response = await llm_manager.chat_with_tools(
                message=chat_request.message,
                tenant_id=chat_request.tenant_id,
                user_id=chat_request.user_id,
                available_tools=TOOLS,
                tool_executor=handle_call_tool
            )
            
            return ChatStreamResponse(
                response=response.content,
                tool_calls=response.tool_calls,
                metadata=response.metadata
            )
            
        except Exception as e:
            logger.error(f"Error en asistente híbrido: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/hybrid/assistant/stream")
    async def mikrotik_assistant_stream(chat_request: ChatMessage):
        """Asistente inteligente con streaming."""
        if not llm_manager or not llm_manager.is_ready():
            raise HTTPException(
                status_code=503, 
                detail="Asistente no disponible"
            )
        
        async def generate_assistant_stream():
            try:
                from mcp_server import TOOLS
                
                async for chunk in llm_manager.chat_with_tools_stream(
                    message=chat_request.message,
                    tenant_id=chat_request.tenant_id,
                    user_id=chat_request.user_id,
                    available_tools=TOOLS,
                    tool_executor=handle_call_tool
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
                    
            except Exception as e:
                logger.error(f"Error en streaming del asistente: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_assistant_stream(),
            media_type="text/plain",
            headers={"Cache-Control": "no-cache"}
        )
    
    @app.get("/hybrid/capabilities")
    async def hybrid_capabilities():
        """Capacidades disponibles en el sistema híbrido."""
        from mcp_server import TOOLS
        
        capabilities = {
            "rest_api": {
                "available": True,
                "endpoints": [
                    "/api/v1/auth/*",
                    "/api/v1/devices/*",
                    "/api/health/*"
                ]
            },
            "mcp_server": {
                "available": True,
                "tools": [tool.name for tool in TOOLS]
            },
            "llm_local": {
                "available": llm_manager is not None and llm_manager.is_ready(),
                "model": llm_manager.model_name if llm_manager else None,
                "capabilities": llm_manager.get_capabilities() if llm_manager else []
            },
            "hybrid_features": {
                "intelligent_assistant": True,
                "tool_integration": True,
                "streaming_chat": True,
                "natural_language_queries": True
            }
        }
        
        return capabilities

# Crear aplicación híbrida
app = create_hybrid_app()

# Endpoint raíz con información del sistema híbrido
@app.get("/")
async def root():
    """Información del sistema híbrido."""
    return {
        "name": "MikroTik Controller - Sistema Híbrido",
        "version": settings.app.app_version,
        "features": {
            "rest_api": "API REST completa en /api/*",
            "mcp_server": "Herramientas MCP en /mcp/*",
            "llm_local": "LLM local en /llm/*",
            "hybrid_assistant": "Asistente inteligente en /hybrid/*"
        },
        "documentation": {
            "rest_api": "/docs",
            "capabilities": "/hybrid/capabilities"
        }
    }

if __name__ == "__main__":
    # Ejecutar aplicación híbrida
    uvicorn.run(
        "app.main_hybrid:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )