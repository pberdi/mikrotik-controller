# Frontend Specification: MikroTik Controller

## Overview

The MikroTik Controller frontend is a modern React-based web application that provides a comprehensive interface for managing MikroTik devices. The application features a real-time dashboard, device management, AI chat integration, and network topology visualization.

## Architecture

### Technology Stack
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **State Management**: Zustand for global state + React Query for server state
- **UI Framework**: Tailwind CSS with Headless UI components
- **Charts**: Recharts for data visualization
- **Real-time**: Socket.io for WebSocket connections
- **Routing**: React Router v6 with lazy loading
- **Forms**: React Hook Form with Zod validation

### Project Structure
```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Basic UI components
│   │   ├── layout/         # Layout components
│   │   ├── charts/         # Chart components
│   │   └── forms/          # Form components
│   ├── pages/              # Page components
│   │   ├── Dashboard/      # Dashboard page
│   │   ├── Devices/        # Device management
│   │   ├── Alerts/         # Alert management
│   │   ├── Topology/       # Network topology
│   │   └── Chat/           # AI chat interface
│   ├── services/           # API and external services
│   │   ├── api.ts          # REST API client
│   │   ├── websocket.ts    # WebSocket service
│   │   └── ai.ts           # AI assistant service
│   ├── stores/             # State management
│   │   ├── auth.ts         # Authentication store
│   │   ├── devices.ts      # Device management store
│   │   ├── alerts.ts       # Alert management store
│   │   └── chat.ts         # AI chat store
│   ├── hooks/              # Custom React hooks
│   ├── utils/              # Utility functions
│   ├── types/              # TypeScript type definitions
│   └── styles/             # Global styles and themes
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
└── tsconfig.json          # TypeScript configuration
```

## Core Features

### 1. Dashboard
- **Real-time Metrics**: Device status, network health, alert summaries
- **Interactive Charts**: Device statistics, performance trends
- **WebSocket Updates**: Live data refresh without page reload
- **Responsive Design**: Works on desktop, tablet, and mobile

### 2. Device Management
- **Device List**: Paginated table with filtering and search
- **Device Details**: Comprehensive device information and status
- **Device Forms**: Create and edit device configurations
- **Bulk Operations**: Multi-select for batch operations
- **Real-time Status**: Live device status updates

### 3. AI Chat Integration
- **Natural Language Interface**: Chat with AI assistant
- **Streaming Responses**: Real-time response generation
- **Command Execution**: Execute device operations through chat
- **Context Awareness**: AI remembers conversation context
- **Multi-language**: Spanish and English support

### 4. Network Topology
- **Interactive Visualization**: D3.js-based network graph
- **Multiple Layouts**: Force-directed, hierarchical, circular
- **Device Interactions**: Click devices for details and actions
- **Zoom and Pan**: Navigate large network topologies
- **Real-time Updates**: Live topology changes

### 5. Alert System
- **Real-time Notifications**: Instant alert display
- **Alert Management**: Acknowledge and resolve alerts
- **Severity Levels**: Critical, warning, info categorization
- **Alert History**: Searchable alert log
- **Notification Grouping**: Prevent notification spam

## Component Architecture

### Layout Components

#### AppLayout
```typescript
interface AppLayoutProps {
  children: React.ReactNode
}

// Features:
// - Responsive sidebar navigation
// - Header with user menu and notifications
// - Theme switching (light/dark)
// - Real-time connection status
```

#### Sidebar
```typescript
interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  currentPath: string
}

// Features:
// - Collapsible navigation menu
// - Active route highlighting
// - Notification badges
// - Mobile-responsive design
```

### Dashboard Components

#### DashboardOverview
```typescript
interface DashboardData {
  deviceStats: DeviceStats
  alertSummary: AlertSummary
  networkHealth: NetworkHealth
  recentActivity: Activity[]
}

// Features:
// - Real-time metrics display
// - Interactive charts and graphs
// - Quick action buttons
// - Responsive grid layout
```

#### MetricsCard
```typescript
interface MetricsCardProps {
  title: string
  value: number | string
  trend?: 'up' | 'down' | 'stable'
  trendValue?: number
  icon?: React.ComponentType
  color?: 'primary' | 'success' | 'warning' | 'error'
}

// Features:
// - Animated value changes
// - Trend indicators
// - Loading states
// - Customizable styling
```

### Device Management Components

#### DeviceList
```typescript
interface DeviceListProps {
  filters?: DeviceFilters
  onDeviceSelect?: (device: Device) => void
  selectionMode?: 'single' | 'multiple' | 'none'
}

// Features:
// - Sortable columns
// - Advanced filtering
// - Bulk selection
// - Pagination
// - Export functionality
```

#### DeviceForm
```typescript
interface DeviceFormProps {
  device?: Device
  onSubmit: (data: DeviceFormData) => void
  onCancel: () => void
  loading?: boolean
}

// Features:
// - Form validation with Zod
// - Secure credential handling
// - Auto-save drafts
// - Error handling
```

### AI Chat Components

#### ChatInterface
```typescript
interface ChatInterfaceProps {
  embedded?: boolean
  height?: string
  onClose?: () => void
}

// Features:
// - Streaming message display
// - Typing indicators
// - Message history
// - Markdown rendering
// - Connection status
```

#### MessageBubble
```typescript
interface MessageBubbleProps {
  message: ChatMessage
  isUser: boolean
  isStreaming?: boolean
}

// Features:
// - User/AI message styling
// - Timestamp display
// - Streaming animation
// - Error states
```

## State Management

### Authentication Store
```typescript
interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  login: (credentials: LoginCredentials) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
}
```

### Device Store
```typescript
interface DeviceStore {
  devices: Map<string, Device>
  stats: DeviceStats | null
  filters: DeviceFilters
  pagination: PaginationState
  loading: boolean
  
  fetchDevices: (filters?: DeviceFilters) => Promise<void>
  createDevice: (data: DeviceCreateData) => Promise<Device>
  updateDevice: (id: string, data: DeviceUpdateData) => Promise<Device>
  deleteDevice: (id: string) => Promise<void>
}
```

### Chat Store
```typescript
interface ChatStore {
  messages: ChatMessage[]
  isConnected: boolean
  isTyping: boolean
  
  sendMessage: (message: string) => Promise<void>
  sendMessageStream: (message: string) => AsyncGenerator<string>
  clearHistory: () => void
}
```

## Real-time Features

### WebSocket Integration
```typescript
class WebSocketService {
  connect(token: string): void
  disconnect(): void
  subscribe(event: string, callback: Function): void
  
  // Supported events:
  // - device_status_changed
  // - new_alert
  // - device_metrics_updated
  // - user_activity
}
```

### Live Updates
- **Device Status**: Real-time device online/offline status
- **Metrics**: Live performance metrics and statistics
- **Alerts**: Instant alert notifications
- **Chat**: Real-time AI responses with streaming

## API Integration

### REST API Service
```typescript
class ApiService {
  // Authentication
  login(credentials: LoginCredentials): Promise<AuthResponse>
  refreshToken(): Promise<TokenResponse>
  
  // Device management
  getDevices(filters?: DeviceFilters): Promise<PaginatedResponse<Device>>
  createDevice(data: DeviceCreateData): Promise<Device>
  updateDevice(id: string, data: DeviceUpdateData): Promise<Device>
  deleteDevice(id: string): Promise<void>
  
  // Statistics
  getDeviceStats(): Promise<DeviceStats>
  getAlertSummary(): Promise<AlertSummary>
}
```

### AI Service Integration
```typescript
class AIService {
  sendMessage(message: string): Promise<string>
  sendMessageStream(message: string): AsyncGenerator<string>
  getCapabilities(): Promise<AICapabilities>
  getStatus(): Promise<AIStatus>
}
```

## Security Features

### Authentication
- JWT token-based authentication
- Automatic token refresh
- Secure token storage
- Session timeout handling

### Data Protection
- Input sanitization and validation
- XSS protection
- CSRF protection
- Secure API communication

### Multi-tenant Support
- Tenant-isolated data display
- Tenant-aware API requests
- Permission-based UI rendering
- Secure tenant switching

## Performance Optimization

### Code Splitting
```typescript
// Route-based code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Devices = lazy(() => import('./pages/Devices'))
const Topology = lazy(() => import('./pages/Topology'))
const Chat = lazy(() => import('./pages/Chat'))
```

### State Optimization
- Memoized selectors
- Selective re-rendering with React.memo
- Debounced search and filters
- Virtual scrolling for large lists

### Bundle Optimization
- Tree shaking for unused code
- Dynamic imports for heavy components
- Optimized asset loading
- CDN for static assets

## Testing Strategy

### Unit Testing
```typescript
// Component testing with React Testing Library
describe('DeviceList', () => {
  it('renders device list correctly', () => {
    render(<DeviceList devices={mockDevices} />)
    expect(screen.getByText('Device List')).toBeInTheDocument()
  })
})
```

### Integration Testing
```typescript
// API integration testing
describe('DeviceService', () => {
  it('fetches devices successfully', async () => {
    const devices = await deviceService.getDevices()
    expect(devices).toHaveLength(5)
  })
})
```

### E2E Testing
```typescript
// Cypress end-to-end testing
describe('Device Management Flow', () => {
  it('creates a new device', () => {
    cy.visit('/devices')
    cy.get('[data-testid="add-device"]').click()
    cy.get('[data-testid="hostname"]').type('test-router')
    cy.get('[data-testid="submit"]').click()
    cy.contains('Device created successfully')
  })
})
```

## Accessibility

### WCAG 2.1 AA Compliance
- Semantic HTML structure
- ARIA labels and descriptions
- Keyboard navigation support
- Color contrast compliance
- Screen reader compatibility

### Implementation
```typescript
// Accessible form components
<label htmlFor="hostname" className="sr-only">
  Device Hostname
</label>
<input
  id="hostname"
  aria-describedby="hostname-help"
  aria-invalid={errors.hostname ? 'true' : 'false'}
/>
```

## Internationalization

### Multi-language Support
```typescript
// i18n configuration
const resources = {
  en: {
    translation: {
      'devices.title': 'Devices',
      'devices.add': 'Add Device'
    }
  },
  es: {
    translation: {
      'devices.title': 'Dispositivos',
      'devices.add': 'Agregar Dispositivo'
    }
  }
}
```

## Deployment

### Development
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run test         # Run tests
npm run lint         # Lint code
```

### Production Build
```dockerfile
# Multi-stage Docker build
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

### Environment Configuration
```typescript
// Environment variables
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_AI_ENABLED=true
VITE_THEME_DEFAULT=light
```