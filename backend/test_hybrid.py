#!/usr/bin/env python3
"""
Script de prueba para el sistema híbrido.

Verifica que todas las funcionalidades estén operativas:
1. API REST
2. MCP Server
3. LLM Local
4. Asistente Híbrido
"""

import asyncio
import json
import sys
from typing import Dict, Any

import httpx

# URLs de prueba
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "root": "/",
    "capabilities": "/hybrid/capabilities",
    "llm_status": "/llm/status",
    "mcp_tools": "/mcp/tools",
    "rest_health": "/api/health"
}

# Datos de prueba
TEST_TENANT_ID = "123e4567-e89b-12d3-a456-426614174000"
TEST_USER_ID = "456e7890-e89b-12d3-a456-426614174000"

async def test_endpoint(client: httpx.AsyncClient, name: str, url: str) -> Dict[str, Any]:
    """Probar un endpoint específico."""
    try:
        response = await client.get(url, timeout=10.0)
        return {
            "name": name,
            "url": url,
            "status": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": "error",
            "success": False,
            "error": str(e)
        }

async def test_mcp_tool(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Probar ejecución de herramienta MCP."""
    try:
        response = await client.post(
            f"{BASE_URL}/mcp/call-tool",
            json={
                "tool_name": "get_device_stats",
                "arguments": {
                    "tenant_id": TEST_TENANT_ID,
                    "user_id": TEST_USER_ID
                }
            },
            timeout=15.0
        )
        
        return {
            "name": "MCP Tool Execution",
            "status": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            "name": "MCP Tool Execution",
            "status": "error",
            "success": False,
            "error": str(e)
        }

async def test_llm_chat(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Probar chat con LLM."""
    try:
        response = await client.post(
            f"{BASE_URL}/llm/chat",
            json={
                "message": "¿Qué es MikroTik?",
                "tenant_id": TEST_TENANT_ID,
                "user_id": TEST_USER_ID
            },
            timeout=30.0
        )
        
        return {
            "name": "LLM Chat",
            "status": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            "name": "LLM Chat",
            "status": "error",
            "success": False,
            "error": str(e)
        }

async def test_hybrid_assistant(client: httpx.AsyncClient) -> Dict[str, Any]:
    """Probar asistente híbrido."""
    try:
        response = await client.post(
            f"{BASE_URL}/hybrid/assistant",
            json={
                "message": "Dame estadísticas de mis dispositivos",
                "tenant_id": TEST_TENANT_ID,
                "user_id": TEST_USER_ID
            },
            timeout=45.0
        )
        
        return {
            "name": "Hybrid Assistant",
            "status": response.status_code,
            "success": response.status_code == 200,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except Exception as e:
        return {
            "name": "Hybrid Assistant",
            "status": "error",
            "success": False,
            "error": str(e)
        }

async def main():
    """Función principal de pruebas."""
    print("🧪 Iniciando pruebas del sistema híbrido...")
    print(f"📍 URL base: {BASE_URL}")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        results = []
        
        # Probar endpoints básicos
        print("1️⃣ Probando endpoints básicos...")
        for name, endpoint in ENDPOINTS.items():
            result = await test_endpoint(client, name, f"{BASE_URL}{endpoint}")
            results.append(result)
            
            status_icon = "✅" if result["success"] else "❌"
            print(f"   {status_icon} {result['name']}: {result['status']}")
        
        print()
        
        # Probar herramienta MCP
        print("2️⃣ Probando herramienta MCP...")
        mcp_result = await test_mcp_tool(client)
        results.append(mcp_result)
        
        status_icon = "✅" if mcp_result["success"] else "❌"
        print(f"   {status_icon} {mcp_result['name']}: {mcp_result['status']}")
        
        print()
        
        # Probar LLM (solo si está disponible)
        print("3️⃣ Probando LLM local...")
        llm_result = await test_llm_chat(client)
        results.append(llm_result)
        
        status_icon = "✅" if llm_result["success"] else "⚠️"
        print(f"   {status_icon} {llm_result['name']}: {llm_result['status']}")
        
        if not llm_result["success"]:
            print("   ℹ️  LLM puede no estar disponible (normal si Ollama no está configurado)")
        
        print()
        
        # Probar asistente híbrido (solo si LLM está disponible)
        if llm_result["success"]:
            print("4️⃣ Probando asistente híbrido...")
            hybrid_result = await test_hybrid_assistant(client)
            results.append(hybrid_result)
            
            status_icon = "✅" if hybrid_result["success"] else "❌"
            print(f"   {status_icon} {hybrid_result['name']}: {hybrid_result['status']}")
        else:
            print("4️⃣ Saltando asistente híbrido (LLM no disponible)")
        
        print()
        print("=" * 60)
        
        # Resumen de resultados
        successful = sum(1 for r in results if r["success"])
        total = len(results)
        
        print(f"📊 Resumen: {successful}/{total} pruebas exitosas")
        
        if successful == total:
            print("🎉 ¡Todas las pruebas pasaron! El sistema híbrido está funcionando correctamente.")
        elif successful >= total * 0.7:
            print("⚠️  La mayoría de las pruebas pasaron. Revisar componentes fallidos.")
        else:
            print("❌ Múltiples componentes fallaron. Revisar configuración.")
        
        print()
        
        # Mostrar detalles de errores
        failed_tests = [r for r in results if not r["success"]]
        if failed_tests:
            print("🔍 Detalles de errores:")
            for test in failed_tests:
                print(f"   • {test['name']}: {test.get('error', test.get('response', 'Error desconocido'))}")
        
        print()
        
        # Mostrar información útil
        print("📋 Información útil:")
        print(f"   • Documentación: {BASE_URL}/docs")
        print(f"   • Capacidades: {BASE_URL}/hybrid/capabilities")
        print(f"   • Estado LLM: {BASE_URL}/llm/status")
        print(f"   • Herramientas MCP: {BASE_URL}/mcp/tools")
        
        # Guardar resultados detallados
        with open("test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"   • Resultados detallados: test_results.json")
        
        return successful == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error ejecutando pruebas: {e}")
        sys.exit(1)