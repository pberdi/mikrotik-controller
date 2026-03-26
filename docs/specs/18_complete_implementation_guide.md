# Complete Implementation Guide: MikroTik Controller

## Overview

This guide provides step-by-step instructions to implement the complete MikroTik Controller system from scratch, including the hybrid backend, AI integration, and React frontend.

## Prerequisites

### System Requirements
- **Operating System**: macOS, Linux, or Windows with WSL2
- **Python**: 3.11+ (recommended 3.11.15)
- **Node.js**: 18+ (recommended 18.17+)
- **PostgreSQL**: 15+ 
- **Redis**: 7+
- **Git**: Latest version

### Development Tools
- **Code Editor**: VS Code with Python and TypeScript extensions
- **API Testing**: Postman or curl
- **Database Client**: pgAdmin or DBeaver
- **Terminal**: bash or zsh

## Phase 1: Backend Implementation

### Step 1: Project Setup
```bash
# Create project directory
mkdir mikrotik-controller
cd mikrotik-controller

# Create backend directory
mkdir backend
cd backend

# Initialize Python virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create basic structure
mkdir -p app/{api/v1,core,models,schemas,services,utils,workers}
mkdir -p tests/{test_services,test_security}
mkdir -p alembic/versions
```

### Step 2: Dependencies Installation
```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.109.0
uvicorn[standard]==0.25.0
sqlalchemy==2.0.25
alembic==1.13.1
psycopg[binary]==3.1.16
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.5.3
pydantic-settings==2.1.0
cryptography==41.0.8
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.2
httpx==0.26.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Database Models
```python
# app/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
```

### Step 4: Core Configuration
```python
# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/mikrotik_controller"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "MikroTik Controller"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 5: Authentication System
```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
```

### Step 6: API Endpoints
```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import Token
from app.services.user_service import UserService
from app.core.security import create_access_token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_service: UserService = Depends()
):
    user = await user_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
```

## Phase 2: Hybrid System Implementation

### Step 1: MCP Server Setup
```bash
# Install MCP dependencies
pip install mcp==1.0.0 ollama==0.1.7

# Create MCP server
cat > mcp_server.py << 'EOF'
from mcp import Server, Tool
from app.services.device_service import DeviceService
from app.core.database import get_db

server = Server("mikrotik-controller-mcp")

@server.tool("list_devices")
async def list_devices(status: str = None):
    """List MikroTik devices with optional status filter"""
    async with get_db() as db:
        device_service = DeviceService(db)
        devices = await device_service.get_devices(status=status)
        return [device.dict() for device in devices]

# Add more tools...
EOF
```

### Step 2: LLM Integration
```bash
# Install Ollama
brew install ollama  # macOS
# or
curl -fsSL https://ollama.ai/install.sh | sh  # Linux

# Start Ollama and download model
ollama serve
ollama pull llama3.2:3b
```

```python
# llm_integration.py
import ollama
from typing import AsyncGenerator

class LLMService:
    def __init__(self):
        self.client = ollama.AsyncClient()
        self.model = "llama3.2:3b"
    
    async def chat(self, message: str) -> str:
        response = await self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": message}]
        )
        return response['message']['content']
    
    async def chat_stream(self, message: str) -> AsyncGenerator[str, None]:
        async for chunk in await self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": message}],
            stream=True
        ):
            yield chunk['message']['content']
```

### Step 3: Hybrid Application
```python
# app/main_hybrid.py
from fastapi import FastAPI
from app.api.v1 import auth, devices
from app.core.database import engine
from app.models.base import Base

# Create hybrid application
app = FastAPI(title="MikroTik Controller - Sistema Híbrido")

# Include traditional API routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])

# Add MCP endpoints
@app.get("/mcp/tools")
async def get_mcp_tools():
    return {"tools": ["list_devices", "get_device", "create_device", ...]}

# Add LLM endpoints
@app.post("/llm/chat")
async def llm_chat(message: str):
    llm_service = LLMService()
    response = await llm_service.chat(message)
    return {"response": response}

# Add hybrid assistant endpoint
@app.post("/hybrid/assistant")
async def hybrid_assistant(message: str, tenant_id: str, user_id: str):
    # Combine LLM + MCP tools automatically
    assistant = HybridAssistant()
    response = await assistant.process_message(message, tenant_id, user_id)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Phase 3: Frontend Implementation

### Step 1: React Project Setup
```bash
# Create frontend directory
cd ../  # Back to project root
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install
npm install @tanstack/react-query zustand axios socket.io-client
npm install @headlessui/react @heroicons/react
npm install tailwindcss @tailwindcss/forms @tailwindcss/typography
npm install react-router-dom react-hook-form @hookform/resolvers zod
npm install recharts d3 @types/d3
```

### Step 2: Project Structure
```bash
# Create directory structure
mkdir -p src/{components/{ui,layout,charts,forms},pages/{Dashboard,Devices,Alerts,Topology,Chat},services,stores,hooks,utils,types}

# Create basic components
touch src/components/layout/{AppLayout,Sidebar,Header}.tsx
touch src/pages/Dashboard/DashboardOverview.tsx
touch src/pages/Devices/{DeviceList,DeviceForm,DeviceCard}.tsx
touch src/pages/Chat/ChatInterface.tsx
```

### Step 3: State Management
```typescript
// src/stores/auth.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  tenant_id: string
  role: string
}

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email: string, password: string) => {
        const response = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
        
        if (response.ok) {
          const data = await response.json()
          set({ 
            token: data.access_token, 
            isAuthenticated: true,
            user: data.user 
          })
        }
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
      }
    }),
    { name: 'auth-storage' }
  )
)
```

### Step 4: API Services
```typescript
// src/services/api.ts
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
})

// Request interceptor for auth token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
    }
    return Promise.reject(error)
  }
)

export default api
```

### Step 5: Dashboard Component
```typescript
// src/pages/Dashboard/DashboardOverview.tsx
import React, { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MetricsCard } from '../../components/ui/MetricsCard'
import { DeviceChart } from '../../components/charts/DeviceChart'
import api from '../../services/api'

interface DashboardData {
  deviceStats: {
    total: number
    online: number
    offline: number
  }
  alerts: {
    critical: number
    warning: number
    info: number
  }
}

export const DashboardOverview: React.FC = () => {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await api.get<DashboardData>('/api/v1/dashboard')
      return response.data
    },
    refetchInterval: 30000 // Refresh every 30 seconds
  })

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <MetricsCard
          title="Total Devices"
          value={data?.deviceStats.total || 0}
          icon={DeviceIcon}
          color="primary"
        />
        <MetricsCard
          title="Online Devices"
          value={data?.deviceStats.online || 0}
          icon={CheckIcon}
          color="success"
        />
        <MetricsCard
          title="Critical Alerts"
          value={data?.alerts.critical || 0}
          icon={AlertIcon}
          color="error"
        />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DeviceChart data={data?.deviceStats} />
        <AlertChart data={data?.alerts} />
      </div>
    </div>
  )
}
```

### Step 6: AI Chat Integration
```typescript
// src/pages/Chat/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react'
import { useChatStore } from '../../stores/chat'
import { MessageBubble } from '../../components/ui/MessageBubble'

export const ChatInterface: React.FC = () => {
  const [message, setMessage] = useState('')
  const { messages, sendMessage, isTyping } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return
    
    await sendMessage(message)
    setMessage('')
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.id}
            message={msg}
            isUser={msg.isUser}
          />
        ))}
        {isTyping && (
          <div className="flex items-center space-x-2">
            <div className="animate-pulse">AI is typing...</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask about your MikroTik devices..."
            className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={!message.trim()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}
```

## Phase 4: Integration and Testing

### Step 1: Backend Testing
```bash
# Create test files
cat > test_hybrid.py << 'EOF'
import asyncio
import httpx
import json

async def test_hybrid_system():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test REST API
        response = await client.get(f"{base_url}/api/v1/health")
        assert response.status_code == 200
        
        # Test MCP tools
        response = await client.get(f"{base_url}/mcp/tools")
        assert response.status_code == 200
        
        # Test LLM
        response = await client.post(
            f"{base_url}/llm/chat",
            json={"message": "Hello"}
        )
        assert response.status_code == 200
        
        # Test hybrid assistant
        response = await client.post(
            f"{base_url}/hybrid/assistant",
            json={
                "message": "¿Cuántos dispositivos tengo?",
                "tenant_id": "test-tenant",
                "user_id": "test-user"
            }
        )
        assert response.status_code == 200

if __name__ == "__main__":
    asyncio.run(test_hybrid_system())
EOF

python test_hybrid.py
```

### Step 2: Frontend Testing
```bash
# Install testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest jsdom

# Create test file
cat > src/components/__tests__/Dashboard.test.tsx << 'EOF'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { DashboardOverview } from '../pages/Dashboard/DashboardOverview'

test('renders dashboard overview', () => {
  const queryClient = new QueryClient()
  
  render(
    <QueryClientProvider client={queryClient}>
      <DashboardOverview />
    </QueryClientProvider>
  )
  
  expect(screen.getByText('Dashboard')).toBeInTheDocument()
})
EOF

npm test
```

## Phase 5: Deployment

### Step 1: Production Configuration
```bash
# Backend production setup
cat > backend/.env.production << 'EOF'
DATABASE_URL=postgresql://user:password@db:5432/mikrotik_controller
REDIS_URL=redis://redis:6379
SECRET_KEY=your-production-secret-key
ENVIRONMENT=production
EOF

# Frontend production build
cd frontend
npm run build
```

### Step 2: Docker Configuration
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-hybrid.txt .
RUN pip install -r requirements-hybrid.txt

COPY . .

CMD ["python", "-m", "app.main_hybrid"]
```

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
```

### Step 3: Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/mikrotik_controller
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mikrotik_controller
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    command: ["ollama", "serve"]

volumes:
  postgres_data:
  ollama_data:
```

## Phase 6: Final Setup and Validation

### Step 1: Complete System Startup
```bash
# Start all services
docker-compose up -d

# Initialize Ollama model
docker-compose exec ollama ollama pull llama3.2:3b

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python seed_database.py
```

### Step 2: System Validation
```bash
# Test all endpoints
curl http://localhost:8000/health
curl http://localhost:8000/mcp/tools
curl http://localhost:8000/hybrid/capabilities

# Test frontend
open http://localhost:3000
```

### Step 3: Performance Verification
- Backend response times < 500ms
- AI responses < 10 seconds
- Frontend load time < 3 seconds
- WebSocket connections stable
- Database queries optimized

## Troubleshooting Guide

### Common Issues
1. **Database connection errors**: Check PostgreSQL service and credentials
2. **LLM not responding**: Verify Ollama service and model download
3. **Frontend API errors**: Check CORS configuration and API URLs
4. **WebSocket failures**: Verify Redis connection and WebSocket endpoints

### Performance Optimization
- Enable database query caching
- Implement API response caching
- Optimize frontend bundle size
- Configure CDN for static assets
- Set up monitoring and alerting

## Maintenance and Updates

### Regular Tasks
- Database backups and maintenance
- Security updates for dependencies
- LLM model updates
- Performance monitoring
- Log rotation and cleanup

### Scaling Considerations
- Horizontal scaling with load balancers
- Database read replicas
- Redis clustering
- Multiple LLM instances
- CDN integration

This complete implementation guide provides all the necessary steps to build the MikroTik Controller system from scratch, including the hybrid backend with AI capabilities and the modern React frontend.