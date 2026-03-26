"""
Integración con LLM local para el Controlador MikroTik.

Este módulo proporciona integración con modelos de lenguaje locales
usando Ollama, llama.cpp, o Transformers para procesamiento de lenguaje natural.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """Proveedores de LLM soportados."""
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    TRANSFORMERS = "transformers"

@dataclass
class ChatResponse:
    """Respuesta del chat con LLM."""
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    """Request para chat con LLM."""
    message: str
    context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None

class LLMManager:
    """
    Manager para LLM local con capacidades de herramientas MCP.
    
    Soporta múltiples proveedores de LLM y integración con herramientas MCP.
    """
    
    def __init__(
        self,
        provider: LLMProvider = LLMProvider.OLLAMA,
        model_name: str = "llama3.2:3b",
        base_url: str = "http://localhost:11434"
    ):
        """
        Inicializar LLM Manager.
        
        Args:
            provider: Proveedor de LLM a usar.
            model_name: Nombre del modelo.
            base_url: URL base del servicio LLM.
        """
        self.provider = provider
        self.model_name = model_name
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None
        self._ready = False
        
        # System prompt para MikroTik
        self.system_prompt = """
Eres un asistente especializado en administración de dispositivos MikroTik.

Tienes acceso a herramientas para:
- Gestionar dispositivos MikroTik (listar, crear, actualizar, eliminar)
- Ver estadísticas y estado de dispositivos
- Consultar logs de auditoría
- Gestionar usuarios y alertas

Cuando el usuario haga preguntas sobre dispositivos MikroTik:
1. Usa las herramientas disponibles para obtener información actualizada
2. Proporciona respuestas claras y útiles
3. Sugiere acciones cuando sea apropiado
4. Explica los resultados en términos comprensibles

Siempre verifica que tengas los IDs de tenant y usuario necesarios antes de usar herramientas.
"""
    
    async def initialize(self) -> None:
        """Inicializar conexión con LLM local."""
        try:
            self.client = httpx.AsyncClient(timeout=30.0)
            
            if self.provider == LLMProvider.OLLAMA:
                await self._initialize_ollama()
            elif self.provider == LLMProvider.LLAMACPP:
                await self._initialize_llamacpp()
            elif self.provider == LLMProvider.TRANSFORMERS:
                await self._initialize_transformers()
            
            self._ready = True
            logger.info(f"LLM {self.provider.value} inicializado: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Error inicializando LLM: {e}")
            self._ready = False
            raise
    
    async def _initialize_ollama(self) -> None:
        """Inicializar Ollama."""
        try:
            # Verificar que Ollama esté corriendo
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            
            # Verificar que el modelo esté disponible
            models = response.json()
            available_models = [model["name"] for model in models.get("models", [])]
            
            if self.model_name not in available_models:
                logger.warning(f"Modelo {self.model_name} no encontrado. Intentando descargar...")
                await self._pull_ollama_model()
            
        except httpx.ConnectError:
            raise ConnectionError(
                f"No se puede conectar a Ollama en {self.base_url}. "
                "Asegúrate de que Ollama esté corriendo: 'ollama serve'"
            )
    
    async def _pull_ollama_model(self) -> None:
        """Descargar modelo en Ollama."""
        logger.info(f"Descargando modelo {self.model_name}...")
        
        response = await self.client.post(
            f"{self.base_url}/api/pull",
            json={"name": self.model_name}
        )
        response.raise_for_status()
        
        # El pull es streaming, esperar a que termine
        async for line in response.aiter_lines():
            if line:
                data = json.loads(line)
                if data.get("status") == "success":
                    logger.info(f"Modelo {self.model_name} descargado exitosamente")
                    break
    
    async def _initialize_llamacpp(self) -> None:
        """Inicializar llama.cpp server."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
        except httpx.ConnectError:
            raise ConnectionError(
                f"No se puede conectar a llama.cpp en {self.base_url}. "
                "Asegúrate de que el servidor esté corriendo."
            )
    
    async def _initialize_transformers(self) -> None:
        """Inicializar Transformers local."""
        # Para Transformers, cargaríamos el modelo directamente
        # Por ahora, simulamos que está disponible
        logger.info("Transformers local inicializado (simulado)")
    
    def is_ready(self) -> bool:
        """Verificar si el LLM está listo."""
        return self._ready
    
    def get_capabilities(self) -> List[str]:
        """Obtener capacidades del LLM."""
        return [
            "chat",
            "tool_calling",
            "streaming",
            "mikrotik_expertise",
            "natural_language_queries"
        ]
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """
        Chat básico con LLM.
        
        Args:
            message: Mensaje del usuario.
            context: Contexto adicional.
            system_prompt: System prompt personalizado.
            
        Returns:
            ChatResponse: Respuesta del LLM.
        """
        if not self.is_ready():
            raise RuntimeError("LLM no está inicializado")
        
        try:
            if self.provider == LLMProvider.OLLAMA:
                return await self._chat_ollama(message, context, system_prompt)
            elif self.provider == LLMProvider.LLAMACPP:
                return await self._chat_llamacpp(message, context, system_prompt)
            else:
                return await self._chat_transformers(message, context, system_prompt)
                
        except Exception as e:
            logger.error(f"Error en chat: {e}")
            raise
    
    async def _chat_ollama(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """Chat con Ollama."""
        prompt = system_prompt or self.system_prompt
        
        # Agregar contexto si está disponible
        if context:
            prompt += f"\n\nContexto adicional: {json.dumps(context, indent=2)}"
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": f"{prompt}\n\nUsuario: {message}\nAsistente:",
                "stream": False
            }
        )
        response.raise_for_status()
        
        result = response.json()
        return ChatResponse(
            content=result["response"],
            metadata={"model": self.model_name, "provider": "ollama"}
        )
    
    async def _chat_llamacpp(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """Chat con llama.cpp."""
        prompt = system_prompt or self.system_prompt
        
        if context:
            prompt += f"\n\nContexto: {json.dumps(context, indent=2)}"
        
        response = await self.client.post(
            f"{self.base_url}/completion",
            json={
                "prompt": f"{prompt}\n\nUsuario: {message}\nAsistente:",
                "n_predict": 512,
                "temperature": 0.7,
                "stop": ["Usuario:", "\n\n"]
            }
        )
        response.raise_for_status()
        
        result = response.json()
        return ChatResponse(
            content=result["content"],
            metadata={"model": self.model_name, "provider": "llamacpp"}
        )
    
    async def _chat_transformers(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> ChatResponse:
        """Chat con Transformers local."""
        # Implementación simulada para Transformers
        return ChatResponse(
            content=f"Respuesta simulada para: {message}",
            metadata={"model": self.model_name, "provider": "transformers"}
        )
    
    async def chat_stream(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Chat con streaming.
        
        Args:
            message: Mensaje del usuario.
            context: Contexto adicional.
            system_prompt: System prompt personalizado.
            
        Yields:
            str: Chunks de la respuesta.
        """
        if not self.is_ready():
            raise RuntimeError("LLM no está inicializado")
        
        try:
            if self.provider == LLMProvider.OLLAMA:
                async for chunk in self._chat_stream_ollama(message, context, system_prompt):
                    yield chunk
            else:
                # Para otros proveedores, simular streaming
                response = await self.chat(message, context, system_prompt)
                words = response.content.split()
                for word in words:
                    yield word + " "
                    await asyncio.sleep(0.05)  # Simular delay
                    
        except Exception as e:
            logger.error(f"Error en streaming: {e}")
            raise
    
    async def _chat_stream_ollama(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Streaming con Ollama."""
        prompt = system_prompt or self.system_prompt
        
        if context:
            prompt += f"\n\nContexto: {json.dumps(context, indent=2)}"
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": f"{prompt}\n\nUsuario: {message}\nAsistente:",
                "stream": True
            }
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break
    
    async def chat_with_tools(
        self,
        message: str,
        tenant_id: str,
        user_id: str,
        available_tools: List[Any],
        tool_executor: Callable
    ) -> ChatResponse:
        """
        Chat con capacidad de usar herramientas MCP.
        
        Args:
            message: Mensaje del usuario.
            tenant_id: ID del tenant.
            user_id: ID del usuario.
            available_tools: Herramientas MCP disponibles.
            tool_executor: Función para ejecutar herramientas.
            
        Returns:
            ChatResponse: Respuesta con posibles llamadas a herramientas.
        """
        # Crear contexto con herramientas disponibles
        tools_context = {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "available_tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                for tool in available_tools
            ]
        }
        
        # Prompt mejorado para uso de herramientas
        enhanced_prompt = f"""
{self.system_prompt}

Herramientas disponibles:
{json.dumps(tools_context['available_tools'], indent=2)}

Para usar una herramienta, responde en este formato:
TOOL_CALL: nombre_herramienta
ARGUMENTS: {{"param1": "valor1", "param2": "valor2"}}

Siempre incluye tenant_id: "{tenant_id}" y user_id: "{user_id}" en los argumentos.

Si no necesitas herramientas, responde normalmente.
"""
        
        # Obtener respuesta del LLM
        response = await self.chat(
            message=message,
            context=tools_context,
            system_prompt=enhanced_prompt
        )
        
        # Verificar si hay llamadas a herramientas
        tool_calls = []
        content = response.content
        
        if "TOOL_CALL:" in content:
            tool_calls = await self._parse_and_execute_tools(
                content, tenant_id, user_id, tool_executor
            )
            
            # Si se ejecutaron herramientas, generar respuesta final
            if tool_calls:
                tool_results = [call.get("result") for call in tool_calls]
                final_prompt = f"""
Basándote en los resultados de las herramientas:
{json.dumps(tool_results, indent=2)}

Responde a la pregunta original del usuario: {message}
Proporciona una respuesta clara y útil basada en los datos obtenidos.
"""
                
                final_response = await self.chat(
                    message="",
                    system_prompt=final_prompt
                )
                content = final_response.content
        
        return ChatResponse(
            content=content,
            tool_calls=tool_calls,
            metadata=response.metadata
        )
    
    async def _parse_and_execute_tools(
        self,
        content: str,
        tenant_id: str,
        user_id: str,
        tool_executor: Callable
    ) -> List[Dict[str, Any]]:
        """Parsear y ejecutar llamadas a herramientas."""
        tool_calls = []
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("TOOL_CALL:"):
                tool_name = line.replace("TOOL_CALL:", "").strip()
                
                # Buscar argumentos en la siguiente línea
                if i + 1 < len(lines) and lines[i + 1].strip().startswith("ARGUMENTS:"):
                    args_line = lines[i + 1].replace("ARGUMENTS:", "").strip()
                    
                    try:
                        arguments = json.loads(args_line)
                        
                        # Asegurar que tenant_id y user_id estén incluidos
                        arguments["tenant_id"] = tenant_id
                        arguments["user_id"] = user_id
                        
                        # Ejecutar herramienta
                        result = await tool_executor(tool_name, arguments)
                        
                        tool_calls.append({
                            "tool": tool_name,
                            "arguments": arguments,
                            "result": result[0].text if result else None
                        })
                        
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
                        tool_calls.append({
                            "tool": tool_name,
                            "error": str(e)
                        })
                
                i += 2  # Saltar TOOL_CALL y ARGUMENTS
            else:
                i += 1
        
        return tool_calls
    
    async def chat_with_tools_stream(
        self,
        message: str,
        tenant_id: str,
        user_id: str,
        available_tools: List[Any],
        tool_executor: Callable
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Chat con herramientas en modo streaming."""
        # Por simplicidad, ejecutar sin streaming y simular chunks
        response = await self.chat_with_tools(
            message, tenant_id, user_id, available_tools, tool_executor
        )
        
        # Simular streaming de la respuesta
        words = response.content.split()
        for i, word in enumerate(words):
            yield {
                "type": "content",
                "content": word + " ",
                "is_final": i == len(words) - 1
            }
            await asyncio.sleep(0.05)
        
        # Enviar información de herramientas al final
        if response.tool_calls:
            yield {
                "type": "tool_calls",
                "tool_calls": response.tool_calls,
                "is_final": True
            }
    
    async def cleanup(self) -> None:
        """Limpiar recursos."""
        if self.client:
            await self.client.aclose()
        self._ready = False
        logger.info("LLM Manager cerrado")