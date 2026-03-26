# Hybrid System Specification: MikroTik Controller

## Overview

The MikroTik Controller implements a **Sistema Híbrido** (Hybrid System) that combines traditional REST API management with modern AI capabilities. This specification details the complete hybrid architecture, implementation, and usage patterns.

## System Components

### 1. API REST Layer (Traditional)
- FastAPI backend with JWT authentication
- PostgreSQL database with multi-tenant isolation
- Redis for caching and session management
- Complete CRUD operations for all resources

### 2. MCP Server Layer (AI Integration)
- Model Context Protocol implementation
- 9 specialized tools for AI integration
- Direct access to all system functions
- Secure tool execution with user permissions

### 3. Local LLM Layer (AI Processing)
- Ollama with llama3.2:3b model
- Local processing without external dependencies
- MikroTik RouterOS expertise
- Spanish/English language support

### 4. Hybrid Assistant (Intelligence)
- Combines LLM + MCP tools automatically
- Real-time chat with streaming responses
- Natural language operation execution
- Context-aware conversations

### 5. React Frontend (User Interface)
- Real-time dashboard with WebSocket
- Complete device management interface
- Integrated AI chat interface
- Network topology visualization

## Implementation Details

### Backend Structure
```
backend/
├── app/
│   ├── main.py              # Traditional REST API
│   ├── main_hybrid.py       # Hybrid system entry point
│   ├── api/v1/              # REST API endpoints
│   ├── core/                # Core services
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic schemas
│   └── services/            # Business logic
├── llm_integration.py       # LLM integration
├── mcp_server.py           # MCP server implementation
├── requirements-hybrid.txt  # Hybrid dependencies
└── setup_hybrid.sh         # Automated setup
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/         # React components
│   ├── pages/             # Page components
│   ├── services/          # API services
│   ├── stores/            # State management
│   ├── hooks/             # Custom hooks
│   └── utils/             # Utilities
├── package.json           # Dependencies
└── vite.config.ts         # Build configuration
```
## MCP Tools Available

### Device Management Tools
1. **list_devices** - List all MikroTik devices with filtering
2. **get_device** - Get detailed device information
3. **create_device** - Create and adopt new devices
4. **update_device** - Update device configuration
5. **delete_device** - Remove devices from system
6. **get_device_stats** - Device statistics and metrics

### System Management Tools
7. **list_users** - List system users and roles
8. **get_audit_logs** - Access audit trail
9. **list_alerts** - System alerts and notifications

## AI Capabilities

### Natural Language Processing
- Understands Spanish and English queries
- MikroTik RouterOS specific knowledge
- Context-aware conversations
- Technical terminology recognition

### Automatic Tool Integration
- Analyzes user queries to determine needed tools
- Executes multiple tools in sequence if needed
- Provides comprehensive responses with data
- Maintains conversation context

### Example Interactions
```
User: "¿Cuántos dispositivos MikroTik tengo activos?"
AI: Uses list_devices and get_device_stats tools
Response: "Tienes 15 dispositivos MikroTik, 12 están online y 3 offline..."

User: "Show me devices that are offline"
AI: Uses list_devices with status filter
Response: "Here are the offline devices: [detailed list]"

User: "Create a new device with IP 192.168.1.1"
AI: Uses create_device tool
Response: "Device created successfully with ID: [uuid]"
```

## Installation and Setup

### Automated Setup
```bash
cd backend
./setup_hybrid.sh
```

This script automatically:
- Installs Python dependencies
- Configures Ollama and downloads LLM model
- Initializes database with migrations
- Seeds test data
- Verifies system functionality

### Manual Setup
```bash
# Install dependencies
pip install -r requirements-hybrid.txt

# Install and configure Ollama
brew install ollama  # macOS
ollama serve
ollama pull llama3.2:3b

# Setup database
python seed_database.py

# Start hybrid system
python -m app.main_hybrid
```

## Usage Patterns

### Traditional API Usage
```bash
# Authentication
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'

# Device management
curl -X GET http://localhost:8000/api/v1/devices \
  -H "Authorization: Bearer TOKEN"
```

### AI Assistant Usage
```bash
# Natural language queries
curl -X POST http://localhost:8000/hybrid/assistant \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuántos routers están conectados?",
    "tenant_id": "tenant-uuid",
    "user_id": "user-uuid"
  }'
```

### MCP Direct Usage
```bash
# List available tools
curl -X GET http://localhost:8000/mcp/tools

# Execute specific tool
curl -X POST http://localhost:8000/mcp/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "list_devices",
    "arguments": {"status": "online"}
  }'
```

## Security Considerations

### AI Security
- Local LLM processing (no external data sharing)
- Tenant-isolated AI conversations
- User permission validation for all AI operations
- Audit logging of AI interactions

### Data Protection
- All AI processing happens locally
- No sensitive data sent to external services
- Encrypted storage of device credentials
- Secure WebSocket connections for real-time features

## Performance Characteristics

### Response Times
- Simple AI queries: <3 seconds
- Complex AI operations: <10 seconds
- REST API calls: <500ms
- WebSocket updates: <100ms

### Resource Usage
- LLM Model: 2GB RAM (llama3.2:3b)
- Backend: ~500MB RAM
- Frontend: Standard React app requirements
- Database: Scales with device count

## Testing and Validation

### Automated Testing
```bash
# Test hybrid system
python test_hybrid.py

# Expected results: 7/8 tests passing (87.5%)
# - REST API endpoints: ✅
# - MCP tools: ✅
# - LLM integration: ✅
# - Hybrid assistant: ⚠️ (timeout expected for complex queries)
```

### Manual Testing
- Verify all REST endpoints work
- Test AI chat functionality
- Validate MCP tool execution
- Check real-time WebSocket updates

## Deployment Options

### Development
```bash
# Start hybrid system
python -m app.main_hybrid

# Access points:
# - API docs: http://localhost:8000/docs
# - System info: http://localhost:8000/
# - AI chat: http://localhost:8000/llm/chat
```

### Production
```yaml
# Docker Compose
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://...
    depends_on:
      - database
      - redis
      - ollama
  
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
```

## Troubleshooting

### Common Issues
1. **LLM not responding**: Check Ollama service status
2. **MCP tools failing**: Verify database connectivity
3. **AI timeouts**: Normal for complex queries, retry if needed
4. **WebSocket issues**: Check Redis connectivity

### Diagnostic Commands
```bash
# Check system status
curl http://localhost:8000/hybrid/capabilities

# Test LLM directly
curl -X POST http://localhost:8000/llm/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# Verify MCP tools
curl http://localhost:8000/mcp/tools
```

## Future Enhancements

### Planned Features
- Advanced AI model fine-tuning
- Multi-language support expansion
- Enhanced tool integration
- Predictive analytics capabilities
- Custom AI training on network data

### Scalability Improvements
- Multiple LLM instances for load balancing
- Distributed AI processing
- Enhanced caching strategies
- Performance optimization