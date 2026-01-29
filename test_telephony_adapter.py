"""
Simple test to validate the telephony adapter interface.
"""
import asyncio
from datetime import datetime
from uuid import uuid4

from backend.telephony.mock import FakeTelephonyAdapter
from backend.telephony.types import CallMetadata, CallDirection


async def test_telephony_adapter():
    """Test the FakeTelephonyAdapter implementation."""
    print("\n" + "=" * 70)
    print("Testing Telephony Adapter Interface")
    print("=" * 70)
    
    # Create adapter instance
    adapter = FakeTelephonyAdapter()
    print("\n✓ FakeTelephonyAdapter initialized")
    
    # Test 1: Register a phone number
    print("\n1. Testing register_number()...")
    tenant_id = uuid4()
    phone_number_id = uuid4()
    did_number = "+15551234567"
    
    result = await adapter.register_number(tenant_id, phone_number_id, did_number)
    assert result['status'] == 'success'
    assert result['did_number'] == did_number
    print(f"✓ Phone number registered: {did_number}")
    print(f"  Result: {result}")
    
    # Test 2: Handle inbound call
    print("\n2. Testing on_inbound_call()...")
    call_metadata = CallMetadata(
        tenant_id=tenant_id,
        phone_number_id=phone_number_id,
        caller_number="+15559876543",
        called_number=did_number,
        direction=CallDirection.INBOUND,
        timestamp=datetime.now(),
        call_id="test-call-123"
    )
    
    call_event = await adapter.on_inbound_call(call_metadata)
    assert call_event.call_metadata.tenant_id == tenant_id
    assert call_event.call_metadata.caller_number == "+15559876543"
    print(f"✓ Inbound call handled")
    print(f"  Event: {call_event.event_type}")
    print(f"  Caller: {call_event.call_metadata.caller_number}")
    print(f"  Details: {call_event.details}")
    
    # Test 3: Unregister phone number
    print("\n3. Testing unregister_number()...")
    result = await adapter.unregister_number(tenant_id, phone_number_id, did_number)
    assert result['status'] == 'success'
    print(f"✓ Phone number unregistered: {did_number}")
    print(f"  Result: {result}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✓ All telephony adapter tests passed!")
    print("=" * 70)
    print("\nNOTE: This was a test of the MOCK adapter only.")
    print("Real telephony adapters (Twilio, Asterisk, etc.) are NOT YET IMPLEMENTED.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_telephony_adapter())
