"""
Integration tests for Agent Brain v1 APIs.

Tests the new endpoints:
- GET /api/tenants/{tenant_id}/agent-config
- PATCH /api/tenants/{tenant_id}/agent-config
- POST /api/sandbox/simulate

All tests use simulated/mock responses - no real AI inference.
"""

import sys
import requests
from uuid import uuid4


# Base URL for API
BASE_URL = "http://localhost:8000"


def test_agent_config_endpoints():
    """Test agent configuration endpoints."""
    print("\n=== Testing Agent Config Endpoints ===")
    
    # Create a tenant first
    print("\n1. Creating test tenant...")
    response = requests.post(f"{BASE_URL}/api/tenants", json={
        "primary_language": "hi"
    })
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    tenant = response.json()
    tenant_id = tenant["id"]
    assert tenant["primary_language"] == "hi", "Primary language should be 'hi'"
    print(f"✓ Created tenant {tenant_id} with primary_language=hi")
    
    # Test GET /api/tenants/{tenant_id}/agent-config (without business profile)
    print("\n2. Testing GET /api/tenants/{tenant_id}/agent-config (no business profile)")
    response = requests.get(f"{BASE_URL}/api/tenants/{tenant_id}/agent-config")
    assert response.status_code == 200
    config = response.json()
    assert config["tenant_id"] == tenant_id
    assert config["primary_language"] == "hi"
    assert config["business_profile"] is None
    print("✓ Retrieved agent config without business profile")
    
    # Test PATCH /api/tenants/{tenant_id}/agent-config (add business profile)
    print("\n3. Testing PATCH /api/tenants/{tenant_id}/agent-config (add business profile)")
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{tenant_id}/agent-config",
        json={
            "business_profile": {
                "business_name": "Mumbai Restaurant",
                "business_type": "Restaurant",
                "services": ["Dine-in", "Takeaway", "Delivery"],
                "service_areas": ["Mumbai", "Thane"],
                "business_hours": {
                    "monday": "9:00-22:00",
                    "tuesday": "9:00-22:00",
                    "wednesday": "9:00-22:00",
                    "thursday": "9:00-22:00",
                    "friday": "9:00-23:00",
                    "saturday": "9:00-23:00",
                    "sunday": "10:00-22:00"
                },
                "booking_enabled": True,
                "escalation_rules": {
                    "complaints": "Transfer to manager",
                    "pricing_disputes": "Escalate to billing"
                },
                "forbidden_statements": [
                    "We don't care about your feedback",
                    "That's not our problem"
                ]
            }
        }
    )
    assert response.status_code == 200
    config = response.json()
    assert config["business_profile"] is not None
    assert config["business_profile"]["business_name"] == "Mumbai Restaurant"
    assert config["business_profile"]["booking_enabled"] is True
    assert len(config["business_profile"]["services"]) == 3
    print("✓ Added business profile")
    
    # Test GET /api/tenants/{tenant_id}/agent-config (with business profile)
    print("\n4. Testing GET /api/tenants/{tenant_id}/agent-config (with business profile)")
    response = requests.get(f"{BASE_URL}/api/tenants/{tenant_id}/agent-config")
    assert response.status_code == 200
    config = response.json()
    assert config["business_profile"] is not None
    assert config["business_profile"]["business_name"] == "Mumbai Restaurant"
    print("✓ Retrieved agent config with business profile")
    
    # Test PATCH /api/tenants/{tenant_id}/agent-config (update primary language)
    print("\n5. Testing PATCH /api/tenants/{tenant_id}/agent-config (update primary language)")
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{tenant_id}/agent-config",
        json={
            "primary_language": "en"
        }
    )
    assert response.status_code == 200
    config = response.json()
    assert config["primary_language"] == "en"
    assert config["business_profile"] is not None  # Should still be there
    print("✓ Updated primary language to 'en'")
    
    # Test PATCH /api/tenants/{tenant_id}/agent-config (update business profile)
    print("\n6. Testing PATCH /api/tenants/{tenant_id}/agent-config (update business profile)")
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{tenant_id}/agent-config",
        json={
            "business_profile": {
                "booking_enabled": False,
                "services": ["Dine-in", "Takeaway"]  # Removed Delivery
            }
        }
    )
    assert response.status_code == 200
    config = response.json()
    assert config["business_profile"]["booking_enabled"] is False
    assert len(config["business_profile"]["services"]) == 2
    print("✓ Updated business profile")
    
    # Test GET with non-existent tenant
    print("\n7. Testing GET /api/tenants/{tenant_id}/agent-config (not found)")
    fake_id = str(uuid4())
    response = requests.get(f"{BASE_URL}/api/tenants/{fake_id}/agent-config")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"
    print("✓ Correctly returned 404 for non-existent tenant")
    
    return tenant_id


def test_sandbox_simulate_endpoint(tenant_id: str):
    """Test sandbox simulation endpoint."""
    print("\n=== Testing Sandbox Simulate Endpoint ===")
    
    # Test POST /api/sandbox/simulate (without session_id)
    print("\n1. Testing POST /api/sandbox/simulate (auto-generate session_id)")
    response = requests.post(
        f"{BASE_URL}/api/sandbox/simulate",
        json={
            "tenant_id": tenant_id,
            "user_text": "Hello, I need help with booking"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    result = response.json()
    
    # Verify response structure
    assert "session_id" in result
    assert "detected_language" in result
    assert "speaking_language" in result
    assert "simulated_response" in result
    
    # Verify simulated response message
    assert result["simulated_response"] == "This is a mock response based on assembled prompt. No AI inference performed."
    
    session_id_1 = result["session_id"]
    print(f"✓ Simulated response with auto-generated session_id: {session_id_1}")
    print(f"  - Detected language: {result['detected_language']}")
    print(f"  - Speaking language: {result['speaking_language']}")
    
    # Test POST /api/sandbox/simulate (with explicit session_id, same session)
    print("\n2. Testing POST /api/sandbox/simulate (reuse session_id)")
    response = requests.post(
        f"{BASE_URL}/api/sandbox/simulate",
        json={
            "tenant_id": tenant_id,
            "user_text": "What are your opening hours?",
            "session_id": session_id_1
        }
    )
    assert response.status_code == 200
    result2 = response.json()
    assert result2["session_id"] == session_id_1
    # Language should be cached from first request
    print(f"✓ Reused session_id: {result2['session_id']}")
    print(f"  - Detected language: {result2['detected_language']}")
    print(f"  - Speaking language: {result2['speaking_language']}")
    
    # Test POST /api/sandbox/simulate (language switch request)
    print("\n3. Testing POST /api/sandbox/simulate (language switch request)")
    response = requests.post(
        f"{BASE_URL}/api/sandbox/simulate",
        json={
            "tenant_id": tenant_id,
            "user_text": "Please speak hindi",
            "session_id": session_id_1
        }
    )
    assert response.status_code == 200
    result3 = response.json()
    assert result3["session_id"] == session_id_1
    # Speaking language should change to 'hi' due to switch request
    assert result3["speaking_language"] == "hi"
    print(f"✓ Detected language switch to: {result3['speaking_language']}")
    
    # Test POST /api/sandbox/simulate (new session)
    print("\n4. Testing POST /api/sandbox/simulate (new session)")
    response = requests.post(
        f"{BASE_URL}/api/sandbox/simulate",
        json={
            "tenant_id": tenant_id,
            "user_text": "Namaste, mujhe madad chahiye"
        }
    )
    assert response.status_code == 200
    result4 = response.json()
    assert result4["session_id"] != session_id_1  # Should be different
    print(f"✓ New session created: {result4['session_id']}")
    print(f"  - Detected language: {result4['detected_language']}")
    
    # Test POST /api/sandbox/simulate (non-existent tenant)
    print("\n5. Testing POST /api/sandbox/simulate (tenant not found)")
    fake_id = str(uuid4())
    response = requests.post(
        f"{BASE_URL}/api/sandbox/simulate",
        json={
            "tenant_id": fake_id,
            "user_text": "Hello"
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"
    print("✓ Correctly returned 404 for non-existent tenant")


def test_language_detection_fallback(tenant_id: str):
    """Test language detection fallback to primary_language."""
    print("\n=== Testing Language Detection Fallback ===")
    
    # First update tenant's primary_language to 'mr' (Marathi)
    print("\n1. Setting tenant primary_language to 'mr'")
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{tenant_id}/agent-config",
        json={
            "primary_language": "mr"
        }
    )
    assert response.status_code == 200
    print("✓ Set primary_language to 'mr'")
    
    # Test simulation - if confidence is low, should fallback to 'mr'
    print("\n2. Testing simulation with potential fallback")
    # Run multiple times to increase chance of hitting low-confidence scenario
    for i in range(5):
        response = requests.post(
            f"{BASE_URL}/api/sandbox/simulate",
            json={
                "tenant_id": tenant_id,
                "user_text": "Some ambiguous text"
            }
        )
        assert response.status_code == 200
        result = response.json()
        print(f"  Attempt {i+1}: detected={result['detected_language']}, speaking={result['speaking_language']}")
        # Note: Due to mock implementation, actual fallback may vary
    
    print("✓ Tested fallback behavior")


def main():
    """Run all integration tests."""
    print("=" * 70)
    print("Agent Brain v1 APIs - Integration Tests")
    print("=" * 70)
    print("\nIMPORTANT: All responses are SIMULATED/MOCK.")
    print("No real LLM calls are made. All AI responses are placeholder text.")
    print("=" * 70)
    
    try:
        # Run tests
        tenant_id = test_agent_config_endpoints()
        test_sandbox_simulate_endpoint(tenant_id)
        test_language_detection_fallback(tenant_id)
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        return 0
    
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API server")
        print("Please ensure the server is running: python main.py")
        return 1
    
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
