#!/bin/bash

# Script de configuración para MCP Server del Controlador MikroTik
# Este script instala las dependencias adicionales necesarias para MCP

set -e

echo "🔧 Configurando MCP Server para Controlador MikroTik..."

# Verificar que estamos en el directorio correcto
if [ ! -f "mcp_server.py" ]; then
    echo "❌ Error: No se encuentra mcp_server.py. Ejecutar desde el directorio backend/"
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

# Instalar dependencias MCP
echo "📦 Instalando dependencias MCP..."
pip install -r requirements-mcp.txt

# Instalar dependencias base si no están instaladas
echo "📦 Verificando dependencias base..."
pip install -r requirements.txt

# Instalar el paquete en modo desarrollo
echo "📦 Instalando paquete en modo desarrollo..."
pip install -e .

# Verificar instalación
echo "🧪 Verificando instalación MCP..."
python -c "
import mcp_server
import app.main
print('✅ MCP Server instalado correctamente')
print('✅ Aplicación base funcional')
"

echo ""
echo "🎉 ¡Configuración MCP completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configurar variables de entorno (.env)"
echo "2. Inicializar base de datos: python seed_database.py"
echo "3. Ejecutar MCP server: python mcp_server.py"
echo ""
echo "📖 Para usar como MCP server:"
echo "   uvx mikrotik-controller-mcp"
echo ""
echo "📖 Para usar como API REST:"
echo "   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"