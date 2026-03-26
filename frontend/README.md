# MikroTik Controller - Frontend

Frontend React moderno con **integración de IA** para el Sistema Híbrido MikroTik Controller.

## 🚀 Características Principales

### 🎨 **Interfaz Moderna**
- **React 18+** con TypeScript y Vite
- **Dashboard en tiempo real** con WebSocket
- **Gestión completa** de dispositivos MikroTik
- **Chat integrado** con asistente IA
- **Visualización de topología** de red interactiva

### 🤖 **Integración con IA**
- **Chat inteligente** integrado en la interfaz
- **Consultas en lenguaje natural** al asistente híbrido
- **Respuestas en tiempo real** con streaming
- **Ejecución de operaciones** por chat

## 🏗️ Arquitectura del Frontend

```
┌─────────────────────────────────────────────────────────────┐
│                 FRONTEND REACT                              │
├─────────────────────────────────────────────────────────────┤
│  🎨 COMPONENTES PRINCIPALES                                │
│  • Dashboard con métricas en tiempo real                   │
│  • Gestión de dispositivos con CRUD completo               │
│  • Chat integrado con asistente IA                         │
│  • Visualización de topología de red                       │
│  • Sistema de alertas y notificaciones                     │
├─────────────────────────────────────────────────────────────┤
│  🔧 STACK TECNOLÓGICO                                     │
│  • React 18+ con TypeScript                                │
│  • Vite para build optimizado                              │
│  • Zustand + React Query para estado                       │
│  • Tailwind CSS + Headless UI                              │
│  • Socket.io para tiempo real                              │
│  • Recharts para gráficos                                  │
├─────────────────────────────────────────────────────────────┤
│  🌐 INTEGRACIÓN BACKEND                                   │
│  • API REST para operaciones tradicionales                 │
│  • WebSocket para actualizaciones en tiempo real           │
│  • Chat directo con asistente híbrido                      │
│  • Streaming de respuestas de IA                           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura del Proyecto

```
frontend/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── ui/             # Componentes UI básicos
│   │   ├── layout/         # Componentes de layout
│   │   ├── charts/         # Componentes de gráficos
│   │   └── forms/          # Componentes de formularios
│   ├── pages/              # Páginas principales
│   │   ├── Dashboard/      # Dashboard principal
│   │   ├── Devices/        # Gestión de dispositivos
│   │   ├── Alerts/         # Sistema de alertas
│   │   ├── Topology/       # Visualización de topología
│   │   └── Chat/           # Interfaz de chat con IA
│   ├── services/           # Servicios de API
│   │   ├── api.ts          # Cliente REST API
│   │   ├── websocket.ts    # Servicio WebSocket
│   │   └── ai.ts           # Servicio de IA
│   ├── stores/             # Gestión de estado
│   │   ├── auth.ts         # Estado de autenticación
│   │   ├── devices.ts      # Estado de dispositivos
│   │   ├── alerts.ts       # Estado de alertas
│   │   └── chat.ts         # Estado del chat IA
│   ├── hooks/              # Hooks personalizados
│   ├── utils/              # Funciones utilitarias
│   ├── types/              # Definiciones TypeScript
│   └── styles/             # Estilos globales
├── public/                 # Assets estáticos
├── package.json           # Dependencias y scripts
├── vite.config.ts         # Configuración de Vite
├── tailwind.config.js     # Configuración de Tailwind
└── tsconfig.json          # Configuración de TypeScript
```

## 🚀 Inicio Rápido

### Prerrequisitos
- **Node.js:** 18+ (recomendado 18.17+)
- **npm:** 9+ o **yarn:** 1.22+
- **Backend:** Sistema híbrido ejecutándose en puerto 8000

### Instalación y Desarrollo

```bash
# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev

# Acceder a la aplicación
# http://localhost:5173
```

### Scripts Disponibles

```bash
# Desarrollo
npm run dev          # Servidor de desarrollo con hot-reload

# Construcción
npm run build        # Build de producción
npm run preview      # Preview del build de producción

# Calidad de código
npm run lint         # Linting con ESLint
npm run type-check   # Verificación de tipos TypeScript

# Testing (cuando esté implementado)
npm run test         # Ejecutar tests
npm run test:ui      # Tests con interfaz visual
npm run coverage     # Reporte de cobertura
```

## 🛠️ Stack Tecnológico

### Core Framework
- **React:** 18.2+ con hooks y componentes funcionales
- **TypeScript:** 5.0+ para tipado estático
- **Vite:** 4.4+ para build rápido y HMR

### Estado y Datos
- **Zustand:** 4.4+ para estado global ligero
- **React Query:** 4.32+ para estado del servidor y cache
- **React Hook Form:** 7.45+ para formularios
- **Zod:** 3.22+ para validación de esquemas

### UI y Estilos
- **Tailwind CSS:** 3.3+ para estilos utilitarios
- **Headless UI:** 1.7+ para componentes accesibles
- **Heroicons:** 2.0+ para iconografía
- **Framer Motion:** 10.16+ para animaciones

### Visualización y Gráficos
- **Recharts:** 2.8+ para gráficos y métricas
- **D3.js:** 7.8+ para visualización de topología
- **Visx:** 3.3+ para gráficos avanzados

### Comunicación
- **Axios:** 1.5+ para HTTP requests
- **Socket.io Client:** 4.7+ para WebSocket
- **React Router:** 6.15+ para navegación

## 🎨 Componentes Principales

### Dashboard
```typescript
// Características principales:
- Métricas en tiempo real de dispositivos
- Gráficos interactivos de estado de red
- Resumen de alertas críticas
- Actividad reciente del sistema
- Actualizaciones WebSocket automáticas
```

### Gestión de Dispositivos
```typescript
// Funcionalidades:
- Lista paginada con filtros avanzados
- Formularios de creación/edición
- Vista detallada de dispositivos
- Operaciones en lote
- Estados en tiempo real
```

### Chat con IA
```typescript
// Características:
- Interfaz de chat moderna
- Streaming de respuestas en tiempo real
- Soporte para markdown
- Historial de conversaciones
- Indicadores de estado de conexión
```

### Visualización de Topología
```typescript
// Capacidades:
- Grafo interactivo de red
- Múltiples algoritmos de layout
- Zoom y pan para navegación
- Información contextual en hover
- Actualizaciones en tiempo real
```

## 🔧 Configuración

### Variables de Entorno
```bash
# .env.local
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_AI_ENABLED=true
VITE_THEME_DEFAULT=light
VITE_DEBUG=false
```

### Configuración de Vite
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
})
```

### Configuración de Tailwind
```javascript
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { /* colores personalizados */ },
        secondary: { /* colores personalizados */ }
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography')
  ]
}
```

## 🤖 Integración con IA

### Servicio de IA
```typescript
// src/services/ai.ts
class AIService {
  async sendMessage(message: string): Promise<string>
  async sendMessageStream(message: string): AsyncGenerator<string>
  async getCapabilities(): Promise<AICapabilities>
}
```

### Hook de Chat
```typescript
// Ejemplo de uso
const { messages, sendMessage, isTyping } = useChat()

// Enviar mensaje al asistente
await sendMessage("¿Cuántos dispositivos están online?")
```

### Ejemplos de Consultas
```typescript
// Consultas que el usuario puede hacer:
"¿Cuántos dispositivos MikroTik tengo?"
"¿Qué routers están desconectados?"
"Dame un resumen del estado de la red"
"¿Ha habido alertas críticas hoy?"
"Muestra los dispositivos con mayor tráfico"
```

## 🧪 Testing (Planificado)

### Framework de Testing
```bash
# Dependencias de testing
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

### Tipos de Tests
```typescript
// Unit Tests - Componentes individuales
describe('DeviceCard', () => {
  it('renders device information correctly', () => {
    // Test implementation
  })
})

// Integration Tests - Flujos completos
describe('Device Management Flow', () => {
  it('creates a new device successfully', () => {
    // Test implementation
  })
})

// E2E Tests - Cypress
describe('Dashboard', () => {
  it('displays real-time metrics', () => {
    // Test implementation
  })
})
```

## 🎯 Características Implementadas

### ✅ Estructura Base
- ✅ Proyecto React + TypeScript + Vite configurado
- ✅ Estructura de directorios organizada
- ✅ Configuración de ESLint y TypeScript
- ✅ Configuración básica de Tailwind CSS

### 🔄 En Desarrollo (Según Especificación)
- 🔄 Componentes de layout (AppLayout, Sidebar)
- 🔄 Dashboard con métricas en tiempo real
- 🔄 Gestión de dispositivos (CRUD completo)
- 🔄 Chat integrado con asistente IA
- 🔄 Visualización de topología de red
- 🔄 Sistema de alertas y notificaciones

### ⏳ Planificado
- ⏳ Testing completo (unit, integration, e2e)
- ⏳ Optimizaciones de rendimiento
- ⏳ Características de accesibilidad
- ⏳ Internacionalización (i18n)
- ⏳ PWA capabilities

## 📖 Documentación de Desarrollo

### Guías de Desarrollo
- **[Especificación Frontend](../.kiro/specs/frontend-mikrotik-controller/design.md)** - Diseño técnico completo
- **[Requerimientos](../.kiro/specs/frontend-mikrotik-controller/requirements.md)** - Requerimientos funcionales
- **[Plan de Tareas](../.kiro/specs/frontend-mikrotik-controller/tasks.md)** - Plan de implementación

### Estándares de Código
```typescript
// Componentes funcionales con TypeScript
interface Props {
  title: string
  onAction: () => void
}

export const Component: React.FC<Props> = ({ title, onAction }) => {
  return (
    <div className="p-4">
      <h1>{title}</h1>
      <button onClick={onAction}>Action</button>
    </div>
  )
}
```

## 🚀 Despliegue

### Build de Producción
```bash
# Crear build optimizado
npm run build

# Preview del build
npm run preview
```

### Docker (Planificado)
```dockerfile
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

## 🤝 Contribución

### Flujo de Desarrollo
1. **Revisar** las especificaciones en `.kiro/specs/frontend-mikrotik-controller/`
2. **Implementar** componentes siguiendo el plan de tareas
3. **Probar** la funcionalidad localmente
4. **Documentar** los cambios realizados
5. **Pull Request** con descripción detallada

### Estándares
- **React:** Componentes funcionales con hooks
- **TypeScript:** Tipado estricto y interfaces claras
- **Estilos:** Tailwind CSS con clases utilitarias
- **Estado:** Zustand para global, React Query para servidor
- **Commits:** Conventional commits

---

**🎨 ¡El futuro de las interfaces MikroTik está aquí!**

**Última Actualización:** 26 de Marzo, 2026  
**Versión:** 0.1.0-dev  
**Estado:** 🔄 En Desarrollo Activo