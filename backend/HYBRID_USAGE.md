# Sistema Híbrido: API REST + MCP + LLM Local

## Descripción

Este sistema combina **tres funcionalidades en una sola aplicación**:

1. **API REST completa** (sin cambios) - Para aplicaciones web/móviles
2. **Servidor MCP integrado** - Para herramientas de IA
3. **LLM local con Ollama** - Para procesamiento de lenguaje natural

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Sistema Híbrido                          │
├─────────────────────────────────────────────────────────────┤
│  FastAPI App (Puerto 8000)                                 │
│  ├── /api/*          → API REST completa (sin cambios)     │
│  ├── /mcp/*          → Endpoints MCP                       │
│  ├── /llm/*          → Chat directo con LLM                │
│  └── /hybrid/*       → Asistente inteligente               │
├─────────────────────────────────────────────────────────────┤
│  Servicios Backend                                          │
│  ├── DeviceService   → Gestión de dispositivos             │
│  ├── UserService     → Gestión de usuarios                 │
│  ├── AuditService    → Logs de auditoría                   │
│  └── AlertService    → Gestión de alertas                  │
├─────────────────────────────────────────────────────────────┤
│  Integración LLM                                            │
│  ├── Ollama          → LLM local (llama3.2:3b)             │
│  ├── MCP Tools       → Herramientas para IA                │
│  └── Tool Executor   → Ejecutor de herramientas            │
├─────────────────────────────────────────────────────────────┤
│  Base de Datos                                              │
│  └── PostgreSQL      → Datos persistentes                  │
└─────────────────────────────────────────────────────────────┘
```

## Instalación y Configuración

### 1. Configuración Automática

```bash
cd backend
./setup_hybrid.sh
```

Este script:
- ✅ Instala todas las dependencias
- ✅ Configura Ollama automáticamente
- ✅ Descarga el modelo LLM (llama3.2:3b)
- ✅ Inicializa la base de datos
- ✅ Verifica que todo funcione

### 2. Configuración Manual

Si prefieres configurar manualmente:

```bash
# 1. Instalar dependencias
pip install -r requirements-hybrid.txt

# 2. Instalar Ollama
# macOS:
brew install ollama

# Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# 3. Iniciar Ollama
ollama serve

# 4. Descargar modelo
ollama pull llama3.2:3b

# 5. Configurar base de datos
python seed_database.py
```

## Uso del Sistema

### 1. Iniciar el Sistema Híbrido

```bash
python -m app.main_hybrid
```

El sistema estará disponible en `http://localhost:8000`

### 2. API REST (Sin Cambios)

Toda la funcionalidad REST existente sigue funcionando igual:

```bash
# Autenticación
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Listar dispositivos
curl -X GET http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Herramientas MCP

Acceso directo a herramientas MCP vía HTTP:

```bash
# Listar herramientas disponibles
curl http://localhost:8000/mcp/tools

# Ejecutar herramienta
curl -X POST http://localhost:8000/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "list_devices",
    "arguments": {
      "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
      "page": 1,
      "page_size": 5
    }
  }'
```

### 4. Chat Directo con LLM

Interacción directa con el LLM local:

```bash
# Estado del LLM
curl http://localhost:8000/llm/status

# Chat simple
curl -X POST http://localhost:8000/llm/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explícame qué es MikroTik",
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "456e7890-e89b-12d3-a456-426614174000"
  }'

# Chat con streaming
curl -X POST http://localhost:8000/llm/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cómo configurar un router MikroTik?",
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "456e7890-e89b-12d3-a456-426614174000"
  }'
```

### 5. Asistente Inteligente (Híbrido)

El asistente combina LLM + herramientas MCP automáticamente:

```bash
# Pregunta que requiere datos reales
curl -X POST http://localhost:8000/hybrid/assistant \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuántos dispositivos MikroTik tengo activos?",
    "tenant_id": "123e4567-e89b-12d3-a456-426614174000",
    "user_id": "456e7890-e89b-12d3-a456-426614174000"
  }'

# El asistente automáticamente:
# 1. Usa la herramienta list_devices
# 2. Analiza los resultados
# 3. Responde en lenguaje natural
```

## Ejemplos de Uso del Asistente

### Consultas sobre Dispositivos

```bash
# ¿Cuántos dispositivos tengo?
"message": "¿Cuántos dispositivos MikroTik tengo en total?"

# ¿Cuáles están offline?
"message": "¿Qué dispositivos están desconectados?"

# Crear nuevo dispositivo
"message": "Agrega un nuevo router MikroTik con IP 192.168.1.1, usuario admin y contraseña password123"
```

### Consultas sobre Usuarios

```bash
# Listar usuarios
"message": "¿Qué usuarios están registrados en el sistema?"

# Usuarios inactivos
"message": "¿Hay usuarios inactivos que deba revisar?"
```

### Consultas de Auditoría

```bash
# Actividad reciente
"message": "¿Qué actividad ha habido en los últimos días?"

# Errores de autenticación
"message": "¿Ha habido intentos de login fallidos?"
```

### Consultas sobre Alertas

```bash
# Alertas activas
"message": "¿Hay alertas críticas que requieran atención?"

# Estado general
"message": "Dame un resumen del estado general del sistema"
```

## Capacidades del Sistema

### Verificar Capacidades

```bash
curl http://localhost:8000/hybrid/capabilities
```

Respuesta:
```json
{
  "rest_api": {
    "available": true,
    "endpoints": ["/api/v1/auth/*", "/api/v1/devices/*", "/api/health/*"]
  },
  "mcp_server": {
    "available": true,
    "tools": ["list_devices", "get_device", "create_device", ...]
  },
  "llm_local": {
    "available": true,
    "model": "llama3.2:3b",
    "capabilities": ["chat", "tool_calling", "streaming", "mikrotik_expertise"]
  },
  "hybrid_features": {
    "intelligent_assistant": true,
    "tool_integration": true,
    "streaming_chat": true,
    "natural_language_queries": true
  }
}
```

## Integración con Frontend

### JavaScript/TypeScript

```javascript
// Chat con el asistente
async function chatWithAssistant(message, tenantId, userId) {
  const response = await fetch('/hybrid/assistant', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      tenant_id: tenantId,
      user_id: userId
    })
  });
  
  return await response.json();
}

// Streaming chat
async function streamChat(message, tenantId, userId) {
  const response = await fetch('/hybrid/assistant/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      tenant_id: tenantId,
      user_id: userId
    })
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        console.log('Chunk:', data);
      }
    }
  }
}
```

### React Component

```jsx
import { useState } from 'react';

function MikroTikAssistant({ tenantId, userId }) {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const result = await fetch('/hybrid/assistant', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          tenant_id: tenantId,
          user_id: userId
        })
      });
      
      const data = await result.json();
      setResponse(data.response);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Pregunta sobre tus dispositivos MikroTik..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Procesando...' : 'Enviar'}
        </button>
      </form>
      
      {response && (
        <div>
          <h3>Respuesta:</h3>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
}
```

## Configuración Avanzada

### Variables de Entorno

```bash
# .env
# Configuración LLM
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434

# Configuración existente de la API
DATABASE_URL=postgresql://user:pass@localhost/mikrotik_controller
SECRET_KEY=your-secret-key
```

### Modelos LLM Alternativos

```bash
# Modelos más pequeños (más rápidos)
ollama pull llama3.2:1b

# Modelos más grandes (más precisos)
ollama pull llama3.1:8b
ollama pull codellama:7b

# Cambiar modelo en el código
LLM_MODEL=llama3.1:8b
```

## Monitoreo y Logs

### Logs del Sistema

```bash
# Ver logs en tiempo real
tail -f logs/hybrid_system.log

# Logs específicos del LLM
tail -f logs/llm_integration.log

# Logs de herramientas MCP
tail -f logs/mcp_tools.log
```

### Métricas

```bash
# Estado del sistema
curl http://localhost:8000/hybrid/capabilities

# Estado del LLM
curl http://localhost:8000/llm/status

# Herramientas MCP disponibles
curl http://localhost:8000/mcp/tools
```

## Troubleshooting

### Problemas Comunes

1. **Ollama no conecta**
   ```bash
   # Verificar que Ollama esté corriendo
   ollama serve
   
   # Verificar puerto
   curl http://localhost:11434/api/tags
   ```

2. **Modelo no encontrado**
   ```bash
   # Listar modelos disponibles
   ollama list
   
   # Descargar modelo
   ollama pull llama3.2:3b
   ```

3. **Error de memoria**
   ```bash
   # Usar modelo más pequeño
   ollama pull llama3.2:1b
   ```

4. **Base de datos no conecta**
   ```bash
   # Verificar configuración
   python -c "from app.core.database import engine; print(engine.url)"
   
   # Reinicializar
   python seed_database.py
   ```

### Logs de Debug

```bash
# Activar logs detallados
export LOG_LEVEL=DEBUG
python -m app.main_hybrid
```

## Ventajas del Sistema Híbrido

1. **Sin pérdida de funcionalidad**: API REST completa intacta
2. **LLM local**: Sin dependencias externas, privacidad total
3. **Integración inteligente**: LLM puede usar herramientas automáticamente
4. **Escalable**: Fácil agregar más herramientas y capacidades
5. **Flexible**: Múltiples formas de interactuar (REST, MCP, Chat, Híbrido)

## Próximos Pasos

1. **Agregar más herramientas MCP**: Templates, Jobs, Backups
2. **Mejorar prompts**: Especializar más en MikroTik
3. **Agregar memoria**: Conversaciones persistentes
4. **WebSocket**: Chat en tiempo real
5. **Interfaz web**: Frontend para el asistente
6. **Autenticación**: Integrar JWT con chat
7. **Multimodal**: Soporte para imágenes/diagramas

¿Te gustaría que implemente alguna de estas mejoras o tienes preguntas específicas sobre el uso del sistema híbrido?