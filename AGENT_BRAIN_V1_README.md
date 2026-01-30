# Agent Brain v1 APIs - Implementation Documentation

## Overview

This document describes the implementation of Agent Brain v1 APIs for the VCA multi-tenant Voice AI SaaS platform. **IMPORTANT**: All AI responses are SIMULATED/MOCK. No real LLM calls are made.

## Key Features Implemented

### 1. Multi-Language Support

#### Primary Language Enum
- Added `PrimaryLanguage` enum to Tenant model
- Supported languages: `en` (English), `hi` (Hindi), `mr` (Marathi), `gu` (Gujarati)
- Default: `en`

#### Language Detection Service (`app/services/language_detection.py`)
- **SIMULATED** language detection (no real NLP)
- Session-based detection (cached per session_id)
- Confidence threshold: `LANGUAGE_DETECTION_CONFIDENCE_THRESHOLD = 0.65`
- Fallback to tenant's `primary_language` when confidence < 0.65
- Mock detection uses simple keyword matching for testing

#### Language Switch Detector (`app/services/language_switch.py`)
- **SIMULATED** language switch detection
- Detects explicit language change requests (e.g., "speak hindi", "in english")
- Updates session-specific `speaking_language`
- Locks `speaking_language` after explicit change (prevents auto-switching)
- Pattern-based detection for testing purposes

### 2. Business Profile Model

New `BusinessProfile` model added (`app/models/__init__.py`):

```python
class BusinessProfile(Base):
    tenant_id: UUID (FK to tenants, unique, one-to-one)
    business_name: String(255)
    business_type: String(100)
    services: JSON (list of strings)
    service_areas: JSON (list of strings)
    business_hours: JSON (dict, e.g., {"monday": "9-5"})
    booking_enabled: Boolean
    escalation_rules: JSON (dict)
    forbidden_statements: JSON (list of strings)
```

**Tenant Isolation**: Each business profile belongs to exactly one tenant (one-to-one relationship).

### 3. Runtime Context Builder

Service: `app/services/runtime_context.py`

**Purpose**: Assembles runtime context from configuration WITHOUT calling any LLM.

**Components assembled**:
1. Global agent rules (universal behavior guidelines)
2. Language-specific templates (greetings, acknowledgments, questions)
3. Business profile information (name, type, services, hours, rules)
4. User input (optional)

**Output**: Plain text prompt assembled from configuration. NO AI INFERENCE is performed.

### 4. API Endpoints

#### GET `/api/tenants/{tenant_id}/agent-config`

Retrieves agent configuration for a tenant.

**Response**:
```json
{
  "tenant_id": "uuid",
  "primary_language": "en|hi|mr|gu",
  "business_profile": {
    "id": "uuid",
    "tenant_id": "uuid",
    "business_name": "string",
    "business_type": "string",
    "services": ["string"],
    "service_areas": ["string"],
    "business_hours": {"day": "hours"},
    "booking_enabled": boolean,
    "escalation_rules": {"condition": "action"},
    "forbidden_statements": ["string"],
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

**Status Codes**:
- `200 OK`: Configuration retrieved
- `404 Not Found`: Tenant not found

#### PATCH `/api/tenants/{tenant_id}/agent-config`

Updates agent configuration (primary language and/or business profile).

**Request Body**:
```json
{
  "primary_language": "en|hi|mr|gu",  // optional
  "business_profile": {                // optional
    "business_name": "string",         // required on create
    "business_type": "string",         // required on create
    "services": ["string"],            // optional
    "service_areas": ["string"],       // optional
    "business_hours": {"day": "hours"}, // optional
    "booking_enabled": boolean,        // optional
    "escalation_rules": {},            // optional
    "forbidden_statements": []         // optional
  }
}
```

**Behavior**:
- Creates business profile if it doesn't exist (requires `business_name` and `business_type`)
- Updates existing business profile if it exists
- Only updates provided fields (partial updates supported)

**Status Codes**:
- `200 OK`: Configuration updated
- `400 Bad Request`: Missing required fields when creating business profile
- `404 Not Found`: Tenant not found

#### POST `/api/sandbox/simulate`

**SIMULATES** an agent response based on configuration. NO REAL AI INFERENCE.

**Request Body**:
```json
{
  "tenant_id": "uuid",
  "user_text": "string",
  "session_id": "string"  // optional, auto-generated if not provided
}
```

**Response**:
```json
{
  "session_id": "uuid",
  "detected_language": "en|hi|mr|gu",
  "speaking_language": "en|hi|mr|gu",
  "simulated_response": "This is a mock response based on assembled prompt. No AI inference performed."
}
```

**Behavior**:
1. Generates `session_id` if not provided
2. Detects language from `user_text` (SIMULATED, cached per session)
3. Checks for explicit language switch request
4. Updates `speaking_language` if switch detected (locks it)
5. Assembles runtime context (NO LLM CALL)
6. Returns MOCK response with session information

**Status Codes**:
- `200 OK`: Simulation completed
- `404 Not Found`: Tenant not found

### 5. Session Management

**Session Behavior**:
- Each `session_id` maintains its own state:
  - Detected language (cached after first detection)
  - Speaking language (updated on explicit switch, locked after switch)
- Language detection occurs once per session
- Language switch locks the speaking language for that session
- Services maintain in-memory session state (not persisted)

### 6. Database Updates

**New Tables**:
- `business_profiles` table added with full tenant isolation

**Modified Tables**:
- `tenants` table: Added `primary_language` enum column (default: 'en')

**Migrations**:
- Run `python create_tables.py` to create/update tables

## Testing

### Integration Tests

File: `test_agent_brain_v1.py`

**Test Coverage**:
1. ✅ Agent config endpoints (GET, PATCH)
2. ✅ Business profile creation and updates
3. ✅ Primary language updates
4. ✅ Sandbox simulation with auto-generated session_id
5. ✅ Session reuse and language caching
6. ✅ Language switch detection
7. ✅ Fallback to primary_language
8. ✅ Error handling (404s)

**Running Tests**:
```bash
# Start the server
python main.py

# Run tests in another terminal
python test_agent_brain_v1.py
```

**Expected Output**: All tests should pass with "✓ ALL TESTS PASSED"

### Manual Testing with curl

```bash
# 1. Create tenant with primary language
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"primary_language": "hi"}'

# 2. Get agent config
curl http://localhost:8000/api/tenants/{tenant_id}/agent-config

# 3. Update agent config with business profile
curl -X PATCH http://localhost:8000/api/tenants/{tenant_id}/agent-config \
  -H "Content-Type: application/json" \
  -d '{
    "business_profile": {
      "business_name": "Test Restaurant",
      "business_type": "Restaurant",
      "services": ["Dine-in", "Delivery"],
      "booking_enabled": true
    }
  }'

# 4. Simulate agent response
curl -X POST http://localhost:8000/api/sandbox/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "{tenant_id}",
    "user_text": "Hello, I need help"
  }'

# 5. Simulate with session reuse
curl -X POST http://localhost:8000/api/sandbox/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "{tenant_id}",
    "user_text": "What are your hours?",
    "session_id": "{session_id_from_previous_response}"
  }'

# 6. Simulate language switch
curl -X POST http://localhost:8000/api/sandbox/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "{tenant_id}",
    "user_text": "Please speak hindi",
    "session_id": "{session_id}"
  }'
```

## Important Notes

### 🚨 SIMULATION ONLY

**This implementation contains NO real AI**:
- Language detection: Mock keyword-based detection
- Language switching: Pattern matching for common phrases
- AI responses: Always returns fixed mock text
- Runtime context: Assembles text but doesn't call LLM

**All responses clearly state**: "This is a mock response based on assembled prompt. No AI inference performed."

### Tenant Isolation

All features strictly enforce tenant isolation:
- BusinessProfile has one-to-one relationship with Tenant
- All queries filter by `tenant_id`
- No cross-tenant data access

### No External Dependencies

Per requirements:
- ❌ No telephony/SIP integration
- ❌ No audio processing
- ❌ No real LLM calls (OpenAI, etc.)
- ❌ No outbound calling
- ❌ No billing/analytics
- ❌ No authentication (to be added separately)

### Session State

- In-memory only (not persisted)
- Resets when service restarts
- Production would use Redis or similar for persistence

## API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both include:
- Full endpoint descriptions
- Request/response schemas
- Interactive testing interface
- Examples

## Files Modified/Created

### New Files
- `app/services/__init__.py` - Services package
- `app/services/language_detection.py` - Language detection service
- `app/services/language_switch.py` - Language switch detector
- `app/services/runtime_context.py` - Runtime context builder
- `app/api/agent_config.py` - Agent config endpoints
- `app/api/sandbox.py` - Sandbox simulation endpoint
- `test_agent_brain_v1.py` - Integration tests
- `AGENT_BRAIN_V1_README.md` - This documentation

### Modified Files
- `app/models/__init__.py` - Added PrimaryLanguage enum and BusinessProfile model
- `app/schemas/__init__.py` - Added schemas for agent config and sandbox APIs
- `app/api/__init__.py` - Registered new routers
- `app/api/tenant.py` - Fixed to include primary_language in tenant creation
- `main.py` - Registered agent_config and sandbox routers
- `create_tables.py` - Added BusinessProfile to imports

## Future Enhancements (TODOs)

1. Real language detection using NLP models
2. Real LLM integration for agent responses
3. Redis persistence for session state
4. Webhook notifications
5. Analytics and reporting
6. Authentication and authorization
7. Rate limiting
8. Audit logging

## Contact

For questions or issues, refer to the main VCA repository documentation.
