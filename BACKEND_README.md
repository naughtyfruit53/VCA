# VCA Backend - FastAPI Application

This is the FastAPI backend for the Voice AI Agent (VCA) platform, implementing strict multi-tenant SaaS architecture.

## 🔒 Multi-Tenant Architecture

**CRITICAL**: All resources in this application are strictly isolated by `tenant_id`. 

- Every database model includes a `tenant_id` foreign key
- All API endpoints must enforce tenant isolation
- No global data access is permitted
- Future features MUST follow this pattern

## Project Structure

```
VCA/
├── app/
│   ├── __init__.py
│   ├── api/              # API endpoints
│   │   ├── __init__.py
│   │   └── health.py     # Health check endpoint
│   ├── config/           # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py   # Environment config with fail-fast validation
│   │   └── database.py   # Database connection setup
│   ├── models/           # SQLAlchemy database models
│   │   └── __init__.py   # Tenant, PhoneNumber, Call, AIProfile
│   └── schemas/          # Pydantic request/response schemas
│       └── __init__.py   # API validation schemas
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment variables
└── .gitignore            # Git ignore patterns
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in required values:

```bash
cp .env.example .env
```

**Required environment variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `APP_ENV` - Environment (development/staging/production)
- `APP_NAME` - Application name (default: VCA)
- `DEBUG` - Debug mode (true/false)

### 3. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Health Check
- `GET /healthz` - Health check endpoint (validates configuration)
- `GET /` - Root endpoint (API information)

### Tenant Management
- `POST /api/tenants` - Create a new tenant (status=active by default)
- `GET /api/tenants/{tenant_id}` - Get tenant details by ID
- `PATCH /api/tenants/{tenant_id}` - Update tenant status or plan

**Constraints:**
- Only `status` and `plan` fields can be updated
- Valid status values: `active`, `suspended`, `deleted`
- Valid plan values: `starter`, `growth`, `custom`

### Phone Number Management
- `POST /api/tenants/{tenant_id}/phone-numbers` - Attach a phone number to a tenant
- `GET /api/tenants/{tenant_id}/phone-numbers` - List all phone numbers for a tenant
- `PATCH /api/tenants/{tenant_id}/phone-numbers/{phone_number_id}` - Update phone number (activate/deactivate)

**Constraints:**
- `did_number` must be globally unique across all tenants
- `provider_type` must be set to `"generic"`
- `tenant_id` must reference an existing tenant
- Updates enforce tenant ownership (can only update own phone numbers)
- Phone numbers can be activated/deactivated via `is_active` field

### AI Profile Management
- `POST /api/tenants/{tenant_id}/ai-profiles` - Create an AI profile for a tenant
- `GET /api/tenants/{tenant_id}/ai-profiles` - List all AI profiles for a tenant
- `PATCH /api/tenants/{tenant_id}/ai-profiles/{ai_profile_id}` - Update AI profile

**Constraints:**
- `system_prompt` is required and must be non-empty
- Only one AI profile can have `is_default=True` per tenant
- Setting a profile as default automatically unsets other defaults for that tenant
- Valid role values: `receptionist`, `sales`, `support`, `dispatcher`, `custom`
- Updates enforce tenant ownership (can only update own AI profiles)

### Error Responses
All endpoints return appropriate HTTP status codes:
- `200 OK` - Successful GET/PATCH request
- `201 Created` - Successful POST request
- `400 Bad Request` - Invalid input data or validation failure
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists (e.g., duplicate phone number)
- `500 Internal Server Error` - Server error (safe error messages, no stack traces)

### Future Endpoints (TODO)
See `main.py` for comprehensive list of planned endpoints. All will enforce tenant isolation.

## Database Models

### Tenant
- Core tenant/organization model
- Tracks subscription plan and status
- Parent of all other tenant-scoped resources

### PhoneNumber
- DID numbers assigned to tenants
- Maps incoming calls to specific tenant
- Each number belongs to exactly one tenant

### Call
- Individual phone call records
- Tracks call direction, status, duration
- Belongs to tenant and associated phone number

### AIProfile
- AI agent configuration per tenant
- Defines AI behavior and system prompts
- Supports multiple profiles per tenant

## Configuration

### Fail-Fast Validation
The application uses fail-fast configuration validation:
- Application exits immediately if required env vars are missing
- No fallback values for required configuration
- Health check endpoint reports configuration status

### Environment Variables
All configuration is loaded from environment variables using `python-dotenv`.

## Development Guidelines

### Multi-Tenancy Rules
1. ✅ **Always** include `tenant_id` in new models
2. ✅ **Always** validate `tenant_id` in API endpoints
3. ✅ **Always** filter queries by `tenant_id`
4. ❌ **Never** allow cross-tenant data access
5. ❌ **Never** create global resources without tenant scoping

### Adding New Features
When adding new features:
1. Add `tenant_id` foreign key to any new models
2. Create tenant-scoped API endpoints
3. Enforce tenant isolation in all queries
4. Add appropriate database indexes
5. Update schemas with validation

## Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## Security

- All database models use UUID primary keys
- Tenant isolation enforced at database and API levels
- Configuration validation prevents startup with invalid config
- No sensitive data in logs or error messages (in production)

## Telephony Adapter

### Overview
The telephony adapter provides an abstract interface for integrating with various telephony providers. This design allows the VCA platform to remain provider-agnostic while supporting multiple telephony backends.

### Architecture

#### Design Pattern: Adapter Pattern
The telephony subsystem uses the **Adapter Pattern** to abstract telephony provider implementations:

```
VCA Platform → TelephonyAdapter (Interface) → Concrete Adapters
                                            ├── AsteriskAdapter (TODO)
                                            ├── TwilioAdapter (TODO)
                                            ├── TelnyxAdapter (TODO)
                                            └── FakeTelephonyAdapter (dev/test only)
```

#### Location
All telephony adapter code is located under `backend/telephony/`:
- `adapter.py` - Abstract base class defining the adapter contract
- `types.py` - Data structures for call metadata and events
- `mock.py` - Fake adapter for local development and testing

### Adapter Contract

The `TelephonyAdapter` abstract class defines three core methods that all implementations MUST provide:

#### 1. `register_number(tenant_id, phone_number_id, did_number)`
Registers a phone number with the telephony provider to route incoming calls to the platform.

**Purpose**: Configure telephony system to handle calls for a specific DID
**Tenant Isolation**: YES - all registrations are tenant-scoped
**Returns**: Provider-specific registration details

#### 2. `unregister_number(tenant_id, phone_number_id, did_number)`
Unregisters a phone number from the telephony provider, stopping call routing.

**Purpose**: Remove call routing configuration for a DID
**Tenant Isolation**: YES - all operations are tenant-scoped
**Returns**: Provider-specific unregistration details

#### 3. `on_inbound_call(call_metadata)`
Handles incoming call events from the telephony provider.

**Purpose**: Process new inbound calls and initialize AI conversation
**Tenant Isolation**: YES - call metadata includes tenant_id
**Returns**: CallEvent representing call state

### Data Structures

#### CallMetadata
Represents essential call information without vendor-specific details:
- `tenant_id` - UUID of the tenant (REQUIRED for all calls)
- `phone_number_id` - UUID of the phone number record
- `caller_number` - Caller's phone number
- `called_number` - Called phone number (DID)
- `direction` - INBOUND or OUTBOUND
- `timestamp` - When the call occurred
- `call_id` - External telephony system call ID (optional)

#### CallEvent
Represents a call state transition:
- `event_type` - Type of event (INITIATED, RINGING, ANSWERED, ENDED, FAILED)
- `call_metadata` - Associated call metadata
- `timestamp` - When the event occurred
- `details` - Additional event details (optional)

### Implementation Status

#### ✅ Completed
- Abstract `TelephonyAdapter` interface with method signatures
- Data structures (`CallMetadata`, `CallEvent`)
- `FakeTelephonyAdapter` for development and testing

#### ⚠️ TODO - Concrete Adapters
All concrete telephony provider adapters are **NOT YET IMPLEMENTED**. Each will require:

1. **AsteriskAdapter (SIP-based telephony)**
   - AGI script integration
   - SIP trunk configuration
   - WebRTC support
   - Call recording

2. **TwilioAdapter (Twilio API)**
   - Twilio API authentication
   - Webhook configuration
   - TwiML response generation
   - Call status tracking

3. **TelnyxAdapter (Telnyx API)**
   - Telnyx API authentication
   - Mission Control Portal configuration
   - WebRTC integration
   - Call control commands

### Usage Guidelines

#### For Development/Testing
Use `FakeTelephonyAdapter` for local development:

```python
from backend.telephony.mock import FakeTelephonyAdapter

adapter = FakeTelephonyAdapter()
# All operations are logged but have no real side effects
```

⚠️ **WARNING**: `FakeTelephonyAdapter` is for development ONLY. It logs operations but does NOT interact with real telephony systems.

#### For Production (TODO)
Choose and implement a concrete adapter based on your telephony provider:

```python
# TODO: Import and use real adapter
from backend.telephony.asterisk import AsteriskAdapter  # Not yet implemented

adapter = AsteriskAdapter(config)
```

### Tenant Isolation

**CRITICAL**: All telephony operations MUST enforce tenant isolation:
- Every `register_number` and `unregister_number` call requires `tenant_id`
- All `CallMetadata` objects MUST include `tenant_id`
- Adapters MUST validate tenant ownership before operations
- Cross-tenant access is strictly prohibited

### Integration Points

The telephony adapter integrates with:
1. **Phone Number Management API** - Register/unregister numbers on create/delete
2. **Call Handling System** - Process inbound calls via `on_inbound_call`
3. **AI Agent System** - Route calls to appropriate AI profiles
4. **Call Recording** - Capture and store call audio (TODO)
5. **Call Analytics** - Track call metrics per tenant (TODO)

## TODO

See `main.py` for comprehensive list of planned features:
- Tenant management endpoints
- Phone number management
- Call management
- AI profile management
- Concrete telephony adapter implementations (Asterisk, Twilio, Telnyx)
- AI/LLM integration
- Analytics endpoints
- Billing endpoints
- Webhook configuration

All future features must follow strict tenant isolation patterns.
