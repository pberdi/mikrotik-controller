#!/bin/bash

# Script de configuración para Sistema Híbrido
# API REST + MCP Server + LLM Local

set -e

echo "🚀 Configurando Sistema Híbrido: API REST + MCP + LLM Local..."

# Verificar que estamos en el directorio correcto
if [ ! -f "app/main_hybrid.py" ]; then
    echo "❌ Error: No se encuentra app/main_hybrid.py. Ejecutar desde el directorio backend/"
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "📦 Activando entorno virtual..."
    source venv/bin/activate
else
    echo "⚠️  Advertencia: No se encontró entorno virtual. Creando uno nuevo..."
    python3.11 -m venv venv
    source venv/bin/activate
fi

# Instalar dependencias híbridas
echo "📦 Instalando dependencias híbridas..."
pip install -r requirements-hybrid.txt

# Verificar instalación de Ollama
echo "🤖 Verificando Ollama..."
if command -v ollama &> /dev/null; then
    echo "✅ Ollama encontrado"
    
    # Verificar si Ollama está corriendo
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama está corriendo"
    else
        echo "⚠️  Ollama no está corriendo. Iniciando..."
        ollama serve &
        sleep 5
    fi
    
    # Descargar modelo recomendado si no existe
    echo "📥 Verificando modelo llama3.2:3b..."
    if ! ollama list | grep -q "llama3.2:3b"; then
        echo "📥 Descargando modelo llama3.2:3b (esto puede tomar varios minutos)..."
        ollama pull llama3.2:3b
    else
        echo "✅ Modelo llama3.2:3b ya está disponible"
    fi
else
    echo "⚠️  Ollama no encontrado. Instalando..."
    
    # Detectar sistema operativo e instalar Ollama
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo "❌ Homebrew no encontrado. Instala Ollama manualmente desde https://ollama.ai"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        echo "❌ Sistema operativo no soportado. Instala Ollama manualmente desde https://ollama.ai"
        exit 1
    fi
    
    # Iniciar Ollama
    ollama serve &
    sleep 5
    
    # Descargar modelo
    echo "📥 Descargando modelo llama3.2:3b..."
    ollama pull llama3.2:3b
fi

# Verificar configuración de base de datos
echo "🗄️  Verificando base de datos..."
if [ ! -f ".env" ]; then
    echo "⚠️  Archivo .env no encontrado. Copiando desde .env.example..."
    cp .env.example .env
    echo "📝 Por favor, configura las variables de entorno en .env"
fi

# Inicializar base de datos si es necesario
echo "🗄️  Inicializando base de datos..."
python seed_database.py

# Verificar instalación completa
echo "🧪 Verificando instalación híbrida..."
python -c "
import asyncio
import sys

async def test_imports():
    try:
        # Verificar imports básicos
        import app.main_hybrid
        print('✅ Aplicación híbrida importada')
        
        import llm_integration
        print('✅ Integración LLM importada')
        
        import mcp_server
        print('✅ Servidor MCP importado')
        
        # Verificar conexión a Ollama
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get('http://localhost:11434/api/tags', timeout=5.0)
                if response.status_code == 200:
                    print('✅ Ollama conectado')
                else:
                    print('⚠️  Ollama responde pero con error')
            except Exception as e:
                print(f'⚠️  No se puede conectar a Ollama: {e}')
        
        print('✅ Verificación completada')
        
    except Exception as e:
        print(f'❌ Error en verificación: {e}')
        sys.exit(1)

asyncio.run(test_imports())
"

echo ""
echo "🎉 ¡Configuración híbrida completada!"
echo ""
echo "📋 Sistema configurado con:"
echo "  ✅ API REST completa (FastAPI)"
echo "  ✅ Servidor MCP integrado"
echo "  ✅ LLM local (Ollama + llama3.2:3b)"
echo "  ✅ Asistente inteligente híbrido"
echo ""
echo "🚀 Para iniciar el sistema híbrido:"
echo "   python -m app.main_hybrid"
echo ""
echo "🌐 Endpoints disponibles:"
echo "   • API REST: http://localhost:8000/api/*"
echo "   • MCP Tools: http://localhost:8000/mcp/*"
echo "   • LLM Chat: http://localhost:8000/llm/*"
echo "   • Asistente: http://localhost:8000/hybrid/*"
echo "   • Documentación: http://localhost:8000/docs"
echo ""
echo "🤖 Ejemplo de uso del asistente:"
echo '   curl -X POST http://localhost:8000/hybrid/assistant \'
echo '   -H "Content-Type: application/json" \'
echo '   -d '"'"'{"message": "¿Cuántos dispositivos MikroTik tengo?", "tenant_id": "tu-tenant-id", "user_id": "tu-user-id"}'"'"
echo ""
echo "📖 Para más información, ver HYBRID_USAGE.md"