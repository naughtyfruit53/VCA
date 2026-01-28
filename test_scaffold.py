"""
Test script to validate the FastAPI backend scaffold.

This script tests:
1. Configuration loading and validation
2. Model imports and structure
3. Schema imports
4. API endpoints (health check)
"""

import sys
import requests


def test_configuration():
    """Test configuration loading."""
    print("\n=== Testing Configuration ===")
    try:
        from app.config import settings, is_config_valid
        print(f"✓ Configuration loaded successfully")
        print(f"  - App Name: {settings.app_name}")
        print(f"  - Environment: {settings.app_env}")
        print(f"  - Debug: {settings.debug}")
        print(f"  - Config Valid: {is_config_valid()}")
        return True
    except Exception as e:
        print(f"✗ Configuration failed: {e}")
        return False


def test_models():
    """Test database models."""
    print("\n=== Testing Database Models ===")
    try:
        from app.models import Tenant, PhoneNumber, Call, AIProfile
        from app.models import TenantStatus, TenantPlan, CallDirection, CallStatus, AIRole
        
        print(f"✓ All models imported successfully")
        print(f"  - Tenant: {Tenant.__tablename__}")
        print(f"  - PhoneNumber: {PhoneNumber.__tablename__}")
        print(f"  - Call: {Call.__tablename__}")
        print(f"  - AIProfile: {AIProfile.__tablename__}")
        
        # Verify tenant_id exists in all models
        print("\n✓ Tenant isolation verification:")
        from sqlalchemy import inspect
        
        for model_class, model_name in [
            (PhoneNumber, "PhoneNumber"),
            (Call, "Call"),
            (AIProfile, "AIProfile")
        ]:
            inspector = inspect(model_class)
            tenant_id_col = None
            for col in inspector.columns:
                if col.name == 'tenant_id':
                    tenant_id_col = col
                    break
            
            if tenant_id_col is not None and not tenant_id_col.nullable:
                print(f"  - {model_name}: tenant_id is REQUIRED (nullable=False) ✓")
            else:
                print(f"  - {model_name}: tenant_id missing or nullable! ✗")
                return False
        
        return True
    except Exception as e:
        print(f"✗ Models test failed: {e}")
        return False


def test_schemas():
    """Test Pydantic schemas."""
    print("\n=== Testing Pydantic Schemas ===")
    try:
        from app.schemas import (
            TenantCreate, TenantUpdate, TenantResponse,
            PhoneNumberCreate, PhoneNumberUpdate, PhoneNumberResponse,
            CallCreate, CallUpdate, CallResponse,
            AIProfileCreate, AIProfileUpdate, AIProfileResponse,
            HealthCheckResponse
        )
        print(f"✓ All schemas imported successfully")
        return True
    except Exception as e:
        print(f"✗ Schemas test failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints."""
    print("\n=== Testing API Endpoints ===")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test root endpoint
        print("Testing GET /")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Root endpoint working")
            print(f"  - Name: {data.get('name')}")
            print(f"  - Version: {data.get('version')}")
            print(f"  - Multi-tenant: {data.get('multi_tenant')}")
        else:
            print(f"✗ Root endpoint failed with status {response.status_code}")
            return False
        
        # Test health check endpoint
        print("\nTesting GET /healthz")
        response = requests.get(f"{base_url}/healthz", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check endpoint working")
            print(f"  - Status: {data.get('status')}")
            print(f"  - Config Valid: {data.get('config_valid')}")
            print(f"  - Message: {data.get('message')}")
            
            if not data.get('config_valid'):
                print(f"✗ Configuration is not valid!")
                return False
        else:
            print(f"✗ Health check failed with status {response.status_code}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print(f"✗ Cannot connect to server at {base_url}")
        print("  Make sure the server is running with: python main.py")
        return False
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("VCA Backend Scaffold Validation")
    print("=" * 60)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Models", test_models),
        ("Pydantic Schemas", test_schemas),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed! Backend scaffold is ready.")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed. Please review the output above.")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
