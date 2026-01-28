"""
Integration tests for the Tenant Onboarding & Configuration APIs.

This script validates all the new API endpoints using the existing
test infrastructure and patterns from test_scaffold.py.

To run these tests:
1. Ensure PostgreSQL is running and DATABASE_URL is set in .env
2. Run: python test_api_integration.py
"""

import sys
import requests
from uuid import uuid4


# Base URL for API
BASE_URL = "http://localhost:8000"


def test_tenant_endpoints():
    """Test tenant management endpoints."""
    print("\n=== Testing Tenant Endpoints ===")
    
    # Test POST /api/tenants (create with defaults)
    print("\n1. Testing POST /api/tenants (default values)")
    response = requests.post(f"{BASE_URL}/api/tenants", json={})
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"
    tenant1 = response.json()
    assert tenant1["status"] == "active", "Default status should be 'active'"
    assert tenant1["plan"] == "starter", "Default plan should be 'starter'"
    print(f"✓ Created tenant {tenant1['id']} with default values")
    
    # Test POST /api/tenants (create with custom values)
    print("\n2. Testing POST /api/tenants (custom values)")
    response = requests.post(f"{BASE_URL}/api/tenants", json={
        "status": "suspended",
        "plan": "growth"
    })
    assert response.status_code == 201
    tenant2 = response.json()
    assert tenant2["status"] == "suspended"
    assert tenant2["plan"] == "growth"
    print(f"✓ Created tenant {tenant2['id']} with custom values")
    
    # Test GET /api/tenants/{tenant_id}
    print("\n3. Testing GET /api/tenants/{tenant_id}")
    response = requests.get(f"{BASE_URL}/api/tenants/{tenant1['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tenant1["id"]
    print(f"✓ Retrieved tenant {tenant1['id']}")
    
    # Test GET with non-existent tenant
    print("\n4. Testing GET /api/tenants/{tenant_id} (not found)")
    fake_id = str(uuid4())
    response = requests.get(f"{BASE_URL}/api/tenants/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tenant not found"
    print("✓ Correctly returned 404 for non-existent tenant")
    
    # Test PATCH /api/tenants/{tenant_id}
    print("\n5. Testing PATCH /api/tenants/{tenant_id}")
    response = requests.patch(f"{BASE_URL}/api/tenants/{tenant1['id']}", json={
        "status": "deleted",
        "plan": "custom"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"
    assert data["plan"] == "custom"
    print(f"✓ Updated tenant {tenant1['id']}")
    
    return tenant1, tenant2


def test_phone_number_endpoints(tenant):
    """Test phone number management endpoints."""
    print("\n=== Testing Phone Number Endpoints ===")
    tenant_id = tenant["id"]
    
    # Test POST /api/tenants/{tenant_id}/phone-numbers
    print("\n1. Testing POST /api/tenants/{tenant_id}/phone-numbers")
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/phone-numbers",
        json={
            "tenant_id": tenant_id,
            "did_number": "+15551234567",
            "provider_type": "generic",
            "is_active": True
        }
    )
    assert response.status_code == 201
    phone1 = response.json()
    assert phone1["did_number"] == "+15551234567"
    assert phone1["provider_type"] == "generic"
    print(f"✓ Created phone number {phone1['id']}")
    
    # Test duplicate phone number (should fail with 409)
    print("\n2. Testing duplicate phone number (409 expected)")
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/phone-numbers",
        json={
            "tenant_id": tenant_id,
            "did_number": "+15551234567",
            "provider_type": "generic"
        }
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Phone number already exists"
    print("✓ Correctly rejected duplicate phone number")
    
    # Test invalid provider_type (should fail with 400)
    print("\n3. Testing invalid provider_type (400 expected)")
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/phone-numbers",
        json={
            "tenant_id": tenant_id,
            "did_number": "+15559876543",
            "provider_type": "twilio"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "provider_type must be 'generic'"
    print("✓ Correctly rejected invalid provider_type")
    
    # Create another phone number
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/phone-numbers",
        json={
            "tenant_id": tenant_id,
            "did_number": "+15559876543",
            "provider_type": "generic",
            "is_active": False
        }
    )
    assert response.status_code == 201
    phone2 = response.json()
    
    # Test GET /api/tenants/{tenant_id}/phone-numbers
    print("\n4. Testing GET /api/tenants/{tenant_id}/phone-numbers")
    response = requests.get(f"{BASE_URL}/api/tenants/{tenant_id}/phone-numbers")
    assert response.status_code == 200
    phones = response.json()
    assert len(phones) == 2
    print(f"✓ Retrieved {len(phones)} phone numbers")
    
    # Test PATCH /api/tenants/{tenant_id}/phone-numbers/{phone_number_id}
    print("\n5. Testing PATCH /api/tenants/{tenant_id}/phone-numbers/{phone_number_id}")
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{tenant_id}/phone-numbers/{phone1['id']}",
        json={"is_active": False}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    print(f"✓ Updated phone number {phone1['id']}")
    
    # Test tenant ownership enforcement
    print("\n6. Testing tenant ownership enforcement")
    fake_tenant_id = str(uuid4())
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{fake_tenant_id}/phone-numbers/{phone1['id']}",
        json={"is_active": True}
    )
    assert response.status_code == 404
    assert "does not belong to tenant" in response.json()["detail"]
    print("✓ Correctly enforced tenant ownership")
    
    return phone1, phone2


def test_ai_profile_endpoints(tenant):
    """Test AI profile management endpoints."""
    print("\n=== Testing AI Profile Endpoints ===")
    tenant_id = tenant["id"]
    
    # Test POST /api/tenants/{tenant_id}/ai-profiles
    print("\n1. Testing POST /api/tenants/{tenant_id}/ai-profiles")
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/ai-profiles",
        json={
            "tenant_id": tenant_id,
            "role": "receptionist",
            "system_prompt": "You are a helpful receptionist.",
            "is_default": True
        }
    )
    assert response.status_code == 201
    profile1 = response.json()
    assert profile1["role"] == "receptionist"
    assert profile1["is_default"] is True
    print(f"✓ Created AI profile {profile1['id']}")
    
    # Test empty system_prompt (should fail with 400)
    print("\n2. Testing empty system_prompt (400 expected)")
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/ai-profiles",
        json={
            "tenant_id": tenant_id,
            "role": "sales",
            "system_prompt": ""
        }
    )
    assert response.status_code == 400
    assert "system_prompt is required and cannot be empty" in response.json()["detail"]
    print("✓ Correctly rejected empty system_prompt")
    
    # Create another profile and test default enforcement
    print("\n3. Testing default profile enforcement")
    response = requests.post(
        f"{BASE_URL}/api/tenants/{tenant_id}/ai-profiles",
        json={
            "tenant_id": tenant_id,
            "role": "sales",
            "system_prompt": "You are a sales expert.",
            "is_default": True
        }
    )
    assert response.status_code == 201
    profile2 = response.json()
    assert profile2["is_default"] is True
    
    # Verify first profile is no longer default
    response = requests.get(f"{BASE_URL}/api/tenants/{tenant_id}/ai-profiles")
    profiles = response.json()
    profile1_updated = next(p for p in profiles if p["id"] == profile1["id"])
    assert profile1_updated["is_default"] is False
    print("✓ Correctly enforced one default profile per tenant")
    
    # Test GET /api/tenants/{tenant_id}/ai-profiles
    print("\n4. Testing GET /api/tenants/{tenant_id}/ai-profiles")
    response = requests.get(f"{BASE_URL}/api/tenants/{tenant_id}/ai-profiles")
    assert response.status_code == 200
    profiles = response.json()
    assert len(profiles) == 2
    print(f"✓ Retrieved {len(profiles)} AI profiles")
    
    # Test PATCH /api/tenants/{tenant_id}/ai-profiles/{ai_profile_id}
    print("\n5. Testing PATCH /api/tenants/{tenant_id}/ai-profiles/{ai_profile_id}")
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{tenant_id}/ai-profiles/{profile1['id']}",
        json={
            "role": "support",
            "system_prompt": "You are a support specialist."
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "support"
    assert data["system_prompt"] == "You are a support specialist."
    print(f"✓ Updated AI profile {profile1['id']}")
    
    # Test tenant ownership enforcement
    print("\n6. Testing tenant ownership enforcement")
    fake_tenant_id = str(uuid4())
    response = requests.patch(
        f"{BASE_URL}/api/tenants/{fake_tenant_id}/ai-profiles/{profile1['id']}",
        json={"role": "dispatcher"}
    )
    assert response.status_code == 404
    assert "does not belong to tenant" in response.json()["detail"]
    print("✓ Correctly enforced tenant ownership")
    
    return profile1, profile2


def main():
    """Run all tests."""
    print("=" * 70)
    print("Tenant Onboarding & Configuration APIs - Integration Tests")
    print("=" * 70)
    
    try:
        # Test connectivity
        print("\nTesting API connectivity...")
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"✗ API is not responding correctly")
            return 1
        print("✓ API is reachable")
        
        # Run tests
        tenant1, tenant2 = test_tenant_endpoints()
        test_phone_number_endpoints(tenant1)
        test_ai_profile_endpoints(tenant2)
        
        # Summary
        print("\n" + "=" * 70)
        print("✓ All integration tests passed!")
        print("=" * 70)
        return 0
        
    except requests.exceptions.ConnectionError:
        print(f"\n✗ Cannot connect to server at {BASE_URL}")
        print("  Make sure the server is running with: python main.py")
        return 1
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
