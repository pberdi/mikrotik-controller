# Deployment Guide: MikroTik Controller Platform

## Overview

This document provides comprehensive deployment instructions for the MikroTik Controller Platform, including the Sistema Híbrido (Hybrid System) with AI capabilities and React frontend.

## System Architecture

The platform consists of:
- **Backend API**: FastAPI with PostgreSQL and Redis
- **MCP Server**: Model Context Protocol for AI integration
- **Local LLM**: Ollama with llama3.2:3b model
- **Hybrid Assistant**: AI-powered natural language interface
- **React Frontend**: Modern web interface with real-time features

## Prerequisites

### Hardware Requirements

#### Minimum Requirements
- **CPU**: 4 cores (x86_64 or ARM64)
- **RAM**: 8GB (4GB for LLM, 2GB for backend, 2GB for system)
- **Storage**: 50GB SSD
- **Network**: 100Mbps internet connection

#### Recommended Requirements
- **CPU**: 8 cores (x86_64 or ARM64)
- **RAM**: 16GB (6GB for LLM, 4GB for backend, 6GB for system)
- **Storage**: 100GB NVMe SSD
- **Network**: 1Gbps internet connection

### Software Requirements
- **Operating System**: Ubuntu 22.04 LTS, CentOS 8+, or macOS 12+
- **Docker**: 24.0+ with Docker Compose
- **Python**: 3.11+ (if running without Docker)
- **Node.js**: 18+ (for frontend development)
- **PostgreSQL**: 15+ (if running without Docker)
- **Redis**: 7+ (if running without Docker)

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### Step 1: System Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

#### Step 2: Project Setup
```bash
# Clone or create project directory
mkdir mikrotik-controller
cd mikrotik-controller

# Create directory structure
mkdir -p {backend,frontend,data/{postgres,redis,ollama},config,logs}
```

#### Step 3: Configuration Files
```yaml
# docker-compose.yml
version: '3.8'

services:
  # Backend Hybrid System
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - OLLAMA_URL=http://ollama:11434
      - ENVIRONMENT=production
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - postgres
      - redis
      - ollama
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend React Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    restart: unless-stopped

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./config/postgres.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - ./data/redis:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf:ro
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Ollama LLM Service
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ./data/ollama:/root/.ollama
    ports:
      - "11434:11434"
    environment:
      - OLLAMA_ORIGINS=*
      - OLLAMA_HOST=0.0.0.0
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  ollama_data:

networks:
  default:
    driver: bridge
```