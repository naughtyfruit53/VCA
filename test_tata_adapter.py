"""
Test script for TataTelephonyAdapter implementation.

This script tests the inbound call handling without requiring a real database.
It uses mocks to simulate database operations.
"""
import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4, UUID
from unittest.mock import MagicMock, Mock

# Set up minimal environment
import os
os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/test'
os.environ['APP_ENV'] = 'development'
os.environ['APP_NAME'] = 'VCA'
os.environ['DEBUG'] = 'true'

from backend.telephony.tata import TataTelephonyAdapter
from backend.telephony.types import CallMetadata, CallDirection, CallEventType
from app.models import PhoneNumber, Tenant, Call


def create_mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


def create_mock_phone_number(tenant_id: UUID, did_number: str, is_active: bool = True):
    """Create a mock PhoneNumber object."""
    phone = Mock(spec=PhoneNumber)
    phone.id = uuid4()
    phone.tenant_id = tenant_id
    phone.did_number = did_number
    phone.is_active = is_active
    return phone


def create_mock_call(tenant_id: UUID, phone_number_id: UUID):
    """Create a mock Call object."""
    call = Mock(spec=Call)
    call.id = uuid4()
    call.tenant_id = tenant_id
    call.phone_number_id = phone_number_id
    return call


async def test_on_inbound_call_success():
    """Test successful inbound call handling."""
    print("\n" + "=" * 70)
    print("TEST 1: Successful Inbound Call")
    print("=" * 70)
    
    # Setup
    tenant_id = uuid4()
    did_number = "+15551234567"
    caller_number = "+15559876543"
    call_id = "test-call-123"
    
    mock_phone = create_mock_phone_number(tenant_id, did_number, is_active=True)
    mock_call = create_mock_call(tenant_id, mock_phone.id)
    
    # Mock database session
    db = create_mock_db_session()
    
    # Mock execute to return phone number
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_phone
    db.execute.return_value = mock_result
    
    # Mock commit and refresh for call creation
    db.add.return_value = None
    db.commit.return_value = None
    
    def refresh_side_effect(obj):
        if isinstance(obj, Mock) and obj is not mock_phone:
            obj.id = mock_call.id
    
    db.refresh.side_effect = refresh_side_effect
    
    # Create adapter
    adapter = TataTelephonyAdapter(db)
    
    # Create call metadata
    call_metadata = CallMetadata(
        caller_number=caller_number,
        called_number=did_number,
        direction=CallDirection.INBOUND,
        timestamp=datetime.now(timezone.utc),
        call_id=call_id,
        tenant_id=None,
        phone_number_id=None
    )
    
    # Execute
    call_event = await adapter.on_inbound_call(call_metadata)
    
    # Verify
    assert call_event.event_type == CallEventType.INITIATED, \
        f"Expected INITIATED, got {call_event.event_type}"
    assert call_event.call_metadata.tenant_id == tenant_id, \
        f"Expected tenant_id {tenant_id}, got {call_event.call_metadata.tenant_id}"
    assert call_event.call_metadata.phone_number_id == mock_phone.id, \
        f"Expected phone_number_id {mock_phone.id}, got {call_event.call_metadata.phone_number_id}"
    
    print("✓ Call event type: INITIATED")
    print(f"✓ Tenant ID resolved: {tenant_id}")
    print(f"✓ Phone number ID resolved: {mock_phone.id}")
    print(f"✓ Details: {call_event.details}")
    print("\n✅ TEST PASSED: Successful inbound call handled correctly")


async def test_on_inbound_call_unknown_did():
    """Test inbound call with unknown DID."""
    print("\n" + "=" * 70)
    print("TEST 2: Unknown DID (should fail)")
    print("=" * 70)
    
    # Setup
    did_number = "+15551111111"
    caller_number = "+15559876543"
    call_id = "test-call-456"
    
    # Mock database session - returns None for unknown DID
    db = create_mock_db_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    db.execute.return_value = mock_result
    
    # Create adapter
    adapter = TataTelephonyAdapter(db)
    
    # Create call metadata
    call_metadata = CallMetadata(
        caller_number=caller_number,
        called_number=did_number,
        direction=CallDirection.INBOUND,
        timestamp=datetime.now(timezone.utc),
        call_id=call_id,
        tenant_id=None,
        phone_number_id=None
    )
    
    # Execute
    call_event = await adapter.on_inbound_call(call_metadata)
    
    # Verify
    assert call_event.event_type == CallEventType.FAILED, \
        f"Expected FAILED, got {call_event.event_type}"
    assert "not found" in call_event.details.lower() or "not configured" in call_event.details.lower(), \
        f"Expected 'not found' in details, got: {call_event.details}"
    
    print("✓ Call event type: FAILED")
    print(f"✓ Details: {call_event.details}")
    print("\n✅ TEST PASSED: Unknown DID rejected correctly")


async def test_on_inbound_call_inactive_did():
    """Test inbound call with inactive DID."""
    print("\n" + "=" * 70)
    print("TEST 3: Inactive DID (should fail)")
    print("=" * 70)
    
    # Setup
    tenant_id = uuid4()
    did_number = "+15552222222"
    caller_number = "+15559876543"
    call_id = "test-call-789"
    
    mock_phone = create_mock_phone_number(tenant_id, did_number, is_active=False)
    
    # Mock database session
    db = create_mock_db_session()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_phone
    db.execute.return_value = mock_result
    
    # Create adapter
    adapter = TataTelephonyAdapter(db)
    
    # Create call metadata
    call_metadata = CallMetadata(
        caller_number=caller_number,
        called_number=did_number,
        direction=CallDirection.INBOUND,
        timestamp=datetime.now(timezone.utc),
        call_id=call_id,
        tenant_id=None,
        phone_number_id=None
    )
    
    # Execute
    call_event = await adapter.on_inbound_call(call_metadata)
    
    # Verify
    assert call_event.event_type == CallEventType.FAILED, \
        f"Expected FAILED, got {call_event.event_type}"
    assert "not active" in call_event.details.lower() or "inactive" in call_event.details.lower(), \
        f"Expected 'not active' in details, got: {call_event.details}"
    
    print("✓ Call event type: FAILED")
    print(f"✓ Details: {call_event.details}")
    print("\n✅ TEST PASSED: Inactive DID rejected correctly")


async def test_register_number_not_implemented():
    """Test that register_number raises NotImplementedError."""
    print("\n" + "=" * 70)
    print("TEST 4: register_number (should raise NotImplementedError)")
    print("=" * 70)
    
    # Setup
    db = create_mock_db_session()
    adapter = TataTelephonyAdapter(db)
    
    tenant_id = uuid4()
    phone_number_id = uuid4()
    did_number = "+15553333333"
    
    # Execute and verify
    try:
        await adapter.register_number(tenant_id, phone_number_id, did_number)
        print("❌ TEST FAILED: Should have raised NotImplementedError")
        sys.exit(1)
    except NotImplementedError as e:
        print("✓ Raised NotImplementedError as expected")
        print(f"✓ Message: {str(e)}")
        print("\n✅ TEST PASSED: register_number correctly raises NotImplementedError")


async def test_unregister_number_not_implemented():
    """Test that unregister_number raises NotImplementedError."""
    print("\n" + "=" * 70)
    print("TEST 5: unregister_number (should raise NotImplementedError)")
    print("=" * 70)
    
    # Setup
    db = create_mock_db_session()
    adapter = TataTelephonyAdapter(db)
    
    tenant_id = uuid4()
    phone_number_id = uuid4()
    did_number = "+15554444444"
    
    # Execute and verify
    try:
        await adapter.unregister_number(tenant_id, phone_number_id, did_number)
        print("❌ TEST FAILED: Should have raised NotImplementedError")
        sys.exit(1)
    except NotImplementedError as e:
        print("✓ Raised NotImplementedError as expected")
        print(f"✓ Message: {str(e)}")
        print("\n✅ TEST PASSED: unregister_number correctly raises NotImplementedError")


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("TESTING TataTelephonyAdapter Implementation")
    print("=" * 70)
    
    try:
        await test_on_inbound_call_success()
        await test_on_inbound_call_unknown_did()
        await test_on_inbound_call_inactive_did()
        await test_register_number_not_implemented()
        await test_unregister_number_not_implemented()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nNOTE: These tests use mocks and do not require a real database.")
        print("For integration testing, use a test database with real data.")
        print("=" * 70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
