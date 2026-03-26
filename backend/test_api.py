#!/usr/bin/env python3
"""
Simple API test script to verify the backend is working.

This script tests basic API functionality including:
- Health checks
- Configuration validation
- Database connectivity
"""

import sys
import requests
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(message: str):
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message in red."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message in blue."""
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def print_header(message: str):
    """Print header message."""
    print(f"\n{Colors.BOLD}{message}{Colors.RESET}")


def test_health_check(base_url: str) -> bool:
    """Test basic health check endpoint."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed - Status: {data.get('status')}, Version: {data.get('version')}")
            return True
        else:
            print_error(f"Health check failed - Status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API - Is the server running?")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


def test_readiness_check(base_url: str) -> bool:
    """Test readiness check endpoint (includes dependency checks)."""
    try:
        response = requests.get(f"{base_url}/health/ready", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            dependencies = data.get('dependencies', {})
            
            print_success(f"Readiness check passed - Status: {data.get('status')}")
            
            for dep_name, dep_status in dependencies.items():
                if dep_status in ['healthy', 'connected', 'not_implemented']:
                    print_success(f"  {dep_name}: {dep_status}")
                else:
                    print_warning(f"  {dep_name}: {dep_status}")
            
            return True
        else:
            data = response.json()
            print_error(f"Readiness check failed - Status: {data.get('status')}")
            
            dependencies = data.get('dependencies', {})
            for dep_name, dep_status in dependencies.items():
                print_error(f"  {dep_name}: {dep_status}")
            
            return False
            
    except Exception as e:
        print_error(f"Readiness check error: {e}")
        return False


def test_liveness_check(base_url: str) -> bool:
    """Test liveness check endpoint."""
    try:
        response = requests.get(f"{base_url}/health/live", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Liveness check passed - Status: {data.get('status')}")
            return True
        else:
            print_error(f"Liveness check failed - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Liveness check error: {e}")
        return False


def test_api_docs(base_url: str) -> bool:
    """Test if API documentation is accessible."""
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        
        if response.status_code == 200:
            print_success("API documentation is accessible at /docs")
            return True
        else:
            print_warning("API documentation not accessible (might be disabled in production)")
            return True  # Not a critical failure
            
    except Exception as e:
        print_warning(f"API docs check: {e}")
        return True  # Not a critical failure


def test_openapi_spec(base_url: str) -> bool:
    """Test if OpenAPI specification is accessible."""
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        
        if response.status_code == 200:
            spec = response.json()
            print_success(f"OpenAPI spec accessible - Title: {spec.get('info', {}).get('title')}")
            
            # Count endpoints
            paths = spec.get('paths', {})
            endpoint_count = len(paths)
            print_info(f"  API has {endpoint_count} endpoint paths defined")
            
            return True
        else:
            print_warning("OpenAPI spec not accessible (might be disabled in production)")
            return True  # Not a critical failure
            
    except Exception as e:
        print_warning(f"OpenAPI spec check: {e}")
        return True  # Not a critical failure


def test_cors_headers(base_url: str) -> bool:
    """Test if CORS headers are properly configured."""
    try:
        response = requests.options(
            f"{base_url}/health",
            headers={"Origin": "http://localhost:3000"},
            timeout=5
        )
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials'),
        }
        
        if cors_headers['Access-Control-Allow-Origin']:
            print_success("CORS headers are configured")
            for header, value in cors_headers.items():
                if value:
                    print_info(f"  {header}: {value}")
            return True
        else:
            print_warning("CORS headers not found (might need configuration)")
            return True  # Not a critical failure
            
    except Exception as e:
        print_warning(f"CORS check: {e}")
        return True  # Not a critical failure


def main():
    """Run all API tests."""
    print_header("🧪 MikroTik Controller Backend API Tests")
    
    # Configuration
    base_url = "http://localhost:8000"
    
    print_info(f"Testing API at: {base_url}")
    
    # Run tests
    results = []
    
    print_header("1. Health Checks")
    results.append(("Health Check", test_health_check(base_url)))
    results.append(("Readiness Check", test_readiness_check(base_url)))
    results.append(("Liveness Check", test_liveness_check(base_url)))
    
    print_header("2. API Documentation")
    results.append(("API Docs", test_api_docs(base_url)))
    results.append(("OpenAPI Spec", test_openapi_spec(base_url)))
    
    print_header("3. Configuration")
    results.append(("CORS Headers", test_cors_headers(base_url)))
    
    # Summary
    print_header("📊 Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print()
    if passed == total:
        print_success(f"All tests passed! ({passed}/{total})")
        print()
        print_info("✨ Your API is ready for development!")
        print_info(f"   API: {base_url}")
        print_info(f"   Docs: {base_url}/docs")
        print_info(f"   OpenAPI: {base_url}/openapi.json")
        return 0
    else:
        print_error(f"Some tests failed ({passed}/{total} passed)")
        print()
        print_warning("Please check the errors above and ensure:")
        print_warning("  1. The API server is running")
        print_warning("  2. PostgreSQL is running and accessible")
        print_warning("  3. Redis is running and accessible")
        print_warning("  4. Database migrations have been run")
        return 1


if __name__ == "__main__":
    sys.exit(main())
