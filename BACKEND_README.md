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

---

## Tata SIP + Asterisk Telephony Integration

### Overview
The VCA platform now includes real inbound telephony integration using **Tata SIP** trunk connectivity via **Asterisk** PBX. This integration enables the platform to receive and route incoming phone calls to AI agents with strict tenant isolation.

### Architecture

#### High-Level Flow Diagram
```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────────────┐
│                 │   SIP   │                  │  HTTP   │                      │
│   Tata SIP      │────────▶│    Asterisk      │────────▶│   VCA Platform       │
│   Trunk         │         │    PBX           │  POST   │   (FastAPI)          │
│                 │         │                  │         │                      │
└─────────────────┘         └──────────────────┘         └──────────────────────┘
                                                                     │
                                                                     ▼
                                                          ┌──────────────────────┐
                                                          │                      │
                                                          │   PostgreSQL         │
                                                          │   Database           │
                                                          │   (Multi-tenant)     │
                                                          │                      │
                                                          └──────────────────────┘
```

#### Detailed Call Flow

1. **Inbound SIP Call**
   - Caller dials a DID number provisioned with Tata SIP
   - Tata routes call to Asterisk via SIP trunk (configured in `pjsip.conf`)

2. **Asterisk Call Handling**
   - Asterisk receives call in dialplan context `from-tata-trunk` (configured in `extensions.conf`)
   - Dialplan answers call and captures metadata:
     - `CALLERID(num)` - Caller's phone number (ANI)
     - `EXTEN` - Called DID number (DNIS)
     - `UNIQUEID` - Asterisk's unique call identifier
     - `EPOCH` - Unix timestamp
   - Dialplan POSTs JSON payload to VCA endpoint: `POST /internal/telephony/inbound`

3. **VCA Backend Processing**
   - FastAPI endpoint receives call metadata
   - `TataTelephonyAdapter` resolves DID to `PhoneNumber` record
   - Extracts `tenant_id` from `PhoneNumber` (tenant isolation boundary)
   - Creates `Call` record in database with tenant association
   - Returns success/error response to Asterisk

4. **Call Continuation** (TODO - Future Phase)
   - Initialize AI conversation loop
   - Stream audio to STT service
   - Process with LLM
   - Stream TTS response back to caller
   - Loop until call ends

### Configuration Files

#### 1. pjsip.conf (`backend/telephony/asterisk/pjsip.conf`)
Configures SIP trunk connectivity to Tata SIP service:
- **Transport**: UDP/TCP on port 5060
- **Endpoint**: `tata-trunk` with codec settings (ulaw, alaw, g729)
- **Authentication**: Placeholder credentials (MUST be replaced)
- **AOR**: Tata SIP server address (MUST be configured)
- **Identify**: IP whitelist for Tata servers

⚠️ **SECURITY WARNING**: This file contains PLACEHOLDER credentials only. In production:
- Replace ALL placeholder values with real Tata SIP credentials
- Store file outside git repo (e.g., `/etc/asterisk/pjsip.conf`)
- Set permissions: `chmod 600 pjsip.conf`
- Use secrets management system (Vault, AWS Secrets Manager, etc.)
- NEVER commit real credentials to version control

#### 2. extensions.conf (`backend/telephony/asterisk/extensions.conf`)
Defines call routing dialplan:
- **Context**: `from-tata-trunk` (matches pjsip.conf endpoint)
- **Call Handling**:
  1. Answers call immediately
  2. Captures call variables (caller, DID, call ID, timestamp)
  3. POSTs to VCA backend endpoint via CURL
  4. Handles success/error responses
  5. TODO: AI conversation loop (future phase)
- **Error Handling**: Graceful failure with logging

### Backend Implementation

#### TataTelephonyAdapter (`backend/telephony/tata.py`)
Implements the `TelephonyAdapter` interface for Tata SIP integration:

**Implemented Methods:**
- ✅ `on_inbound_call(call_metadata)` - **FULLY IMPLEMENTED**
  - Resolves DID → `PhoneNumber` → `tenant_id`
  - Creates `Call` record in database
  - Returns `CallEvent` with status
  - Production-safe error handling (no stack traces)
  - Extensive logging at each step

**TODO Methods (Placeholders Only):**
- ⚠️ `register_number(tenant_id, phone_number_id, did_number)` - **NOT IMPLEMENTED**
  - Raises `NotImplementedError`
  - Comment explains required Tata API integration
  - Manual Asterisk configuration required
  
- ⚠️ `unregister_number(tenant_id, phone_number_id, did_number)` - **NOT IMPLEMENTED**
  - Raises `NotImplementedError`
  - Comment explains required Tata API integration
  - Manual Asterisk configuration required

**Tenant Isolation:**
- DID resolution is **STRICT** - no fallback or default tenant
- Every call MUST map to exactly one `PhoneNumber` record
- `PhoneNumber` record determines `tenant_id`
- No cross-tenant data access permitted
- Inactive DIDs are rejected

**Error Handling:**
- All errors are caught and logged with full context
- No stack traces returned to Asterisk (production-safe)
- Clear logging prefixes: `[INBOUND CALL]`
- Database errors trigger rollback

#### Internal API Endpoint (`app/api/telephony.py`)
FastAPI router for internal telephony webhooks:

**Endpoint:**
- `POST /internal/telephony/inbound` - Receives call metadata from Asterisk

**Request Schema:**
```json
{
  "caller_number": "+15551234567",
  "called_number": "+15559876543",
  "call_id": "1706556789.123",
  "timestamp": "1706556789"
}
```

**Response Schema:**
```json
{
  "status": "success",
  "call_record_id": "uuid-here",
  "tenant_id": "tenant-uuid",
  "message": "Call initiated successfully"
}
```

**Security:**
- ⚠️ **INTERNAL ONLY** - Must not be exposed to public internet
- TODO: Authentication header validation (currently logs warning)
- TODO: IP whitelist for Asterisk server(s)
- TODO: Rate limiting to prevent abuse
- Logs all requests with source IP

**Error Handling:**
- Safe error responses (no stack traces)
- HTTP 400 for invalid requests
- HTTP 200 with error status for business logic failures
- Detailed logging for troubleshooting

### Tenant Isolation Architecture

The telephony integration enforces strict tenant boundaries:

1. **DID as Entry Point**
   - Every inbound call arrives on a specific DID number
   - DID is the **only** way to identify which tenant should handle the call

2. **DID → PhoneNumber → Tenant Mapping**
   ```
   DID (+15559876543) ──▶ PhoneNumber Record ──▶ tenant_id (UUID)
                          (database lookup)         (foreign key)
   ```

3. **No Fallbacks**
   - Unknown DID → Call rejected (FAILED event)
   - Inactive DID → Call rejected (FAILED event)
   - Multiple DIDs → Database constraint prevents duplicates
   - No default tenant → Explicit tenant_id required

4. **Database Isolation**
   - `PhoneNumber.tenant_id` foreign key to `Tenant.id`
   - `Call.tenant_id` foreign key to `Tenant.id`
   - All queries filtered by `tenant_id`
   - No cross-tenant JOIN operations

### Security Considerations

#### Credentials Management
- ⚠️ **NO REAL CREDENTIALS IN REPO** - All Asterisk configs have placeholders
- Production deployment MUST:
  - Store configs outside git repo (`/etc/asterisk/`)
  - Use secrets management (Vault, AWS Secrets Manager, etc.)
  - Set file permissions: `chmod 600 pjsip.conf`
  - Rotate credentials regularly

#### Network Security
- Asterisk ↔ VCA communication:
  - Currently HTTP on localhost
  - TODO: Use HTTPS if on separate servers
  - TODO: Add authentication headers
  - TODO: mTLS for service-to-service auth
  
- Asterisk ↔ Tata SIP:
  - SIP trunk on UDP/TCP port 5060
  - TODO: Consider TLS transport (port 5061)
  - Firewall rules to whitelist Tata IPs only
  - RTP media ports (10000-20000 UDP)

#### Internal Endpoint Protection
The `/internal/telephony/inbound` endpoint:
- ✅ Logs all requests with source IP
- ⚠️ TODO: Implement authentication (shared secret, mTLS)
- ⚠️ TODO: IP whitelist enforcement
- ⚠️ TODO: Rate limiting
- ⚠️ MUST NOT be exposed to public internet (use firewall/reverse proxy)

#### Data Security
- Call records include caller phone numbers (PII)
- TODO: Implement call recording encryption
- TODO: Add data retention policies
- TODO: GDPR/privacy compliance features

### Production Deployment Checklist

#### Asterisk Configuration
- [ ] Replace placeholder credentials in `pjsip.conf` with real Tata credentials
- [ ] Update Tata SIP server IPs in `[tata-identify]` section
- [ ] Copy configs to `/etc/asterisk/` (outside git repo)
- [ ] Set ownership and permissions: `chown asterisk:asterisk /etc/asterisk/pjsip.conf && chmod 600 /etc/asterisk/pjsip.conf`
- [ ] Verify codec settings with Tata (ulaw, alaw, g729)
- [ ] Test SIP trunk connectivity with `asterisk -rx "pjsip show endpoints"`
- [ ] Configure firewall rules for SIP (5060) and RTP (10000-20000)
- [ ] Enable Asterisk logging: `/var/log/asterisk/full`
- [ ] Test inbound call routing with test DID

#### VCA Backend Configuration
- [ ] Set `VCA_BACKEND_URL` in `extensions.conf` to correct endpoint
- [ ] Implement authentication for `/internal/telephony/inbound`
- [ ] Configure IP whitelist for Asterisk server(s)
- [ ] Enable production logging (INFO level minimum)
- [ ] Set up monitoring/alerting for:
  - Unknown DIDs (configuration drift)
  - Failed call processing (> 1% failure rate)
  - Database connection errors
  - Asterisk connectivity failures
- [ ] Configure rate limiting on telephony endpoint
- [ ] Enable HTTPS if Asterisk on separate server

#### Database
- [ ] Ensure all DIDs in production are in `phone_numbers` table
- [ ] Verify `tenant_id` associations are correct
- [ ] Set up database backups for call records
- [ ] Configure indexes for call queries (already in models)
- [ ] Monitor database connection pool health

#### Testing
- [ ] Test call with valid DID (should create Call record)
- [ ] Test call with unknown DID (should reject with error)
- [ ] Test call with inactive DID (should reject with error)
- [ ] Verify tenant isolation (call only visible to correct tenant)
- [ ] Load test with expected call volume
- [ ] Test failover scenarios (database down, backend down)

#### Monitoring & Operations
- [ ] Set up call volume metrics per tenant
- [ ] Alert on high call failure rates
- [ ] Monitor Asterisk server health
- [ ] Monitor VCA backend latency
- [ ] Log aggregation (ELK, Splunk, CloudWatch)
- [ ] On-call runbook for telephony issues

### Rationale for Critical Decisions

#### Why Asterisk Instead of Direct SIP Integration?
1. **Mature PBX Features**: Asterisk provides battle-tested SIP trunk management, codec negotiation, NAT traversal, and media handling
2. **Separation of Concerns**: Asterisk handles telephony protocol complexity; VCA focuses on AI/business logic
3. **Flexibility**: Easy to switch providers (Tata → Twilio) without changing VCA code
4. **Call Quality**: Asterisk's media handling and QoS features ensure reliable audio
5. **Future Features**: Built-in support for call recording, conferencing, IVR if needed

#### Why DID-based Tenant Resolution?
1. **Deterministic**: DID uniquely identifies tenant (no ambiguity)
2. **Secure**: No trust in caller-provided data (caller ID can be spoofed)
3. **Simple**: One database lookup, no complex resolution logic
4. **Scalable**: Index on `did_number` makes lookups O(1)
5. **Fail-Safe**: Unknown DID cannot be guessed or defaulted

#### Why Placeholder register_number/unregister_number?
1. **Scope Control**: Problem statement explicitly excludes full provisioning
2. **Provider-Specific**: Tata's provisioning API is not yet known/documented
3. **Manual Override**: Production teams can configure Asterisk directly
4. **Future-Proof**: Interface defined, implementation added when needed
5. **Fail-Explicit**: `NotImplementedError` prevents silent failures

#### Why POST from Asterisk Instead of AGI/ARI?
1. **Decoupling**: HTTP POST is language-agnostic and simple
2. **Reliability**: HTTP has clear success/failure semantics
3. **Monitoring**: HTTP requests are easy to log and monitor
4. **Scalability**: VCA backend can scale independently
5. **Debugging**: Can replay/test with curl or Postman

#### Why Production-Safe Error Handling?
1. **Security**: Stack traces can leak sensitive information
2. **Asterisk Stability**: Never crash Asterisk with malformed responses
3. **Caller Experience**: Errors should fail gracefully (e.g., busy signal)
4. **Operations**: Detailed logs for troubleshooting, safe responses for callers
5. **Compliance**: Error messages should not expose PII or system details

---

## AI Audio Loop for Real-Time Inbound Calls

**Status**: ✅ Backend infrastructure IMPLEMENTED
**Audio Streaming**: ⚠️ Placeholder only (requires ARI External Media)

### Overview

The VCA platform now includes a complete backend infrastructure for AI-powered real-time audio conversations on inbound calls. This system integrates Speech-to-Text (STT), Large Language Model (LLM), and Text-to-Speech (TTS) services to enable autonomous AI agents to handle live phone calls with strict tenant isolation, robust error handling, and non-blocking operations.

### High-Level AI Call Flow

```
Caller → Tata SIP → Asterisk → VCA Backend → AI Loop Handler
                                      ↓
                              AI Services (STT/LLM/TTS)
                                      ↓
                              Redis (Conversation State)
                                      ↓
                              PostgreSQL (Call Records)
```

### Components Implemented

#### 1. AI Services (`backend/ai_services/`)

All AI services follow these principles:
- **Non-blocking**: Async operations with timeout protection
- **Fault-tolerant**: Retry with exponential backoff (2 retries)
- **Graceful failure**: Never crash call, always log errors
- **Tenant-isolated**: All operations respect tenant boundaries

**STT Service** (`stt.py`): OpenAI Whisper for audio transcription
- Model: `whisper-1` (configurable via `STT_MODEL`)
- Timeout: 10s with 2 retries
- Handles empty audio gracefully
- Returns empty string on silence

**LLM Service** (`llm.py`): OpenAI GPT for AI responses
- Model: `gpt-4` (configurable via `LLM_MODEL`)
- Uses tenant's AIProfile system prompt
- Max tokens: 150 (concise responses for phone calls)
- Timeout: 15s with 2 retries
- Fallback responses on failure

**TTS Service** (`tts.py`): OpenAI TTS for voice synthesis
- Model: `tts-1` (configurable via `TTS_MODEL`)
- Voice: `alloy` - neutral, professional (configurable via `TTS_VOICE`)
- Format: MP3 for efficient streaming
- Timeout: 15s with 2 retries
- Truncates long text (500 chars max)

**ARI Client** (`ari_client.py`): Asterisk REST Interface for audio streaming
- ⚠️ **PLACEHOLDER**: Audio streaming not yet implemented
- Provides interface for:
  - Answer calls programmatically
  - Stream audio from caller (TODO: requires External Media)
  - Play audio to caller (TODO: requires External Media)
  - Hang up calls
- Raises `NotImplementedError` for audio streaming methods

**Conversation State Manager** (`conversation_state.py`): Redis-based state tracking
- Tracks per-call conversation history
- Enforces max turns (default: 20) and duration (default: 300s)
- Keys: `call:{call_id}:state` with 1-hour TTL
- Non-blocking async operations
- Atomic updates where possible

#### 2. AI Loop Handler (`backend/ai_services/ai_loop_handler.py`)

Main orchestrator for AI conversations. Coordinates:
- Conversation state initialization in Redis
- AIProfile lookup from database
- ARI connection for audio streaming
- Greeting generation and playback
- Main conversation loop (capture → transcribe → generate → synthesize → play)
- Limit enforcement (max turns, max duration)
- Graceful termination with goodbye message
- Comprehensive error handling at every step
- Latency metric logging (time-to-first-audio)

**Design Principles**:
- **Non-Blocking**: Runs as background task via `asyncio.create_task()`
- **Never Crashes**: All exceptions caught and logged
- **Polite Failures**: AI errors result in apologetic messages, not technical details
- **Observable**: Extensive logging with `[AI LOOP]` prefix

#### 3. Redis Configuration (`app/config/redis.py`)

Connection pool management for conversation state:
- Pool size: 10 connections
- Encoding: UTF-8 with automatic decode
- Lifecycle: Initialize on app startup, close on shutdown
- Health check via ping
- Fail-fast if Redis unavailable

Key naming conventions:
```
call:{call_id}:state       -> JSON conversation state
call:{call_id}:turns       -> Integer turn count
call:{call_id}:started_at  -> Unix timestamp
```

All keys have 1-hour TTL to prevent memory leaks.

#### 4. Integration with Telephony

Modified `backend/telephony/tata.py` to start AI loop:

```python
# After creating Call record in on_inbound_call()
ai_profile = await self._get_ai_profile_for_tenant(tenant_id)

if ai_profile:
    # Start AI loop in background (non-blocking)
    # TODO: Requires channel_id from ARI
    pass
```

**Current Status**: Integration ready but needs `channel_id` from Asterisk to fully enable AI loop.

### Configuration Required

#### Environment Variables (Required)

```bash
# Redis for conversation state
REDIS_URL=redis://localhost:6379/0

# OpenAI API for STT/LLM/TTS
OPENAI_API_KEY=sk-your-key-here

# ARI for audio streaming
ARI_URL=http://localhost:8088
ARI_USERNAME=asterisk
ARI_PASSWORD=asterisk
```

#### Environment Variables (Optional with Defaults)

```bash
# AI Models
STT_MODEL=whisper-1
LLM_MODEL=gpt-4
TTS_MODEL=tts-1
TTS_VOICE=alloy

# Conversation Limits
MAX_CONVERSATION_TURNS=20
MAX_CONVERSATION_DURATION_SECONDS=300
```

### Error Handling Strategy

| Failure | Response | Caller Hears |
|---------|----------|--------------|
| STT failure | Retry 2x, then apologize | "I didn't catch that, please repeat" |
| LLM failure | Retry 2x, then fallback | "Technical difficulty, trying again" |
| TTS failure | Retry 2x, skip audio | "Audio issues, please hold" |
| ARI disconnect | End call gracefully | Call ends |
| Redis error | Log, continue best-effort | May lose history |
| Max turns | Polite goodbye | "Thank you for calling. Goodbye!" |
| Max duration | Polite goodbye | "Maximum call time reached. Thank you!" |

### Latency Targets

- **Time-to-first-audio**: < 5 seconds (logged for monitoring)
- **Per-turn latency**: < 10 seconds total
  - STT: ~2-3s
  - LLM: ~2-4s
  - TTS: ~2-3s
  - Playback: ~1-2s

### Tenant Isolation

All operations enforce strict tenant boundaries:
1. **DID Resolution**: DID → PhoneNumber → tenant_id (one-to-one)
2. **AIProfile**: Each tenant has own system prompts
3. **Conversation State**: Redis keys scoped by call_id (tenant-specific calls)
4. **Call Records**: Database queries filtered by tenant_id
5. **No Cross-Tenant Access**: No shared profiles or conversation data

### Current Limitations

#### ⚠️ ARI Audio Streaming Not Implemented

**Status**: Placeholder methods raise `NotImplementedError`

**Full implementation requires**:
1. ARI External Media setup in Asterisk
2. WebSocket connection for ARI events
3. Audio codec handling (ulaw/alaw → PCM → Whisper format)
4. RTP/WebRTC stream management
5. Voice Activity Detection (VAD) for turn detection
6. Barge-in handling (caller interrupting AI)

**Impact**: Without audio streaming, AI loop cannot capture caller audio or play responses. The orchestration logic is ready, but actual audio flow needs ARI External Media.

**Workaround**: Manual Asterisk dialplan can handle audio for MVP while API provides intelligence layer.

#### 🚧 Features Not Yet Implemented

Marked with TODO in code:

1. **Human Handoff**: Transfer to human agent when requested
2. **DTMF Handling**: Keypress detection for menu navigation
3. **Call Recording**: Full conversation recording with encryption
4. **Feedback Collection**: Post-call satisfaction survey
5. **Multi-Language**: Detect language and switch AI accordingly
6. **Voice Cloning**: Custom branded voice per tenant
7. **Outbound Calls**: Proactive dialing (explicitly out of scope)

### Production Deployment Checklist

#### Prerequisites
- [ ] Redis server installed and accessible
- [ ] OpenAI API key with GPT-4, Whisper, TTS access
- [ ] Asterisk with ARI enabled
- [ ] Each tenant has AIProfile in database

#### Configuration
- [ ] Set REDIS_URL, OPENAI_API_KEY, ARI credentials in environment
- [ ] Verify Redis: `redis-cli ping`
- [ ] Verify OpenAI: Test key in playground
- [ ] Verify ARI: `curl http://localhost:8088/ari/asterisk/info`

#### Testing
- [ ] Test call routing creates Call record
- [ ] Test AI profile lookup for test tenant
- [ ] Monitor first AI call with DEBUG logging
- [ ] Verify time-to-first-audio < 5s
- [ ] Verify graceful handling of AI service failures

#### Monitoring
- [ ] Set up alerts for AI service failures (> 5%)
- [ ] Set up alerts for Redis unavailability
- [ ] Set up alerts for high latency (> 10s)
- [ ] Monitor OpenAI API costs per tenant
- [ ] Track conversation quality metrics

### Troubleshooting

#### AI Loop Not Starting
- Check OPENAI_API_KEY is valid
- Check REDIS_URL is accessible: `redis-cli -u $REDIS_URL ping`
- Check tenant has AIProfile: `SELECT * FROM ai_profiles WHERE tenant_id = '...'`
- Check logs for `[AI LOOP]` messages

#### High Latency
- Check OpenAI API latency in logs
- Check Redis latency: `redis-cli --latency`
- Consider using `gpt-3.5-turbo` instead of `gpt-4`
- Check network connectivity to `api.openai.com`

#### AI Service Failures
- Check OpenAI API quota: https://platform.openai.com/usage
- Check API key validity
- Check rate limits in error messages
- Check OpenAI status page

### Cost Estimation

Per 5-minute call (estimated):
- Whisper STT: ~$0.03
- GPT-4 LLM: ~$0.10-0.20 (depends on conversation length)
- TTS: ~$0.05
- **Total**: ~$0.20-0.30 per call

At 100 calls/month per tenant: ~$20-30/month in OpenAI API costs.

### Rationale for Design Decisions

**Why Non-Blocking?** AI operations take 10-15s. Blocking would prevent Asterisk from handling other calls. Background tasks allow concurrent call handling.

**Why Redis?** Conversation history needs sub-millisecond access for real-time. PostgreSQL too slow for per-turn lookups.

**Why OpenAI for All?** Single vendor for STT/LLM/TTS simplifies integration and billing. Services are abstracted for easy swap later.

**Why Retry 2x?** Handles ~95% of transient network/API failures without excessive latency.

**Why Max 150 Tokens?** Phone conversations need concise responses. Long AI responses = high latency and caller confusion.

**Why Placeholder ARI?** Full External Media requires complex Asterisk configuration. Provide interface now, implement audio later.

### Next Steps

To fully enable AI audio loop:

1. **Implement ARI External Media** in Asterisk
   - Configure `ari.conf` for External Media
   - Set up WebSocket event handling
   - Implement audio codec conversion pipeline
   - Add VAD for turn detection

2. **Pass `channel_id` from Asterisk** to VCA
   - Modify `extensions.conf` to send channel ID
   - Update `/internal/telephony/inbound` endpoint
   - Uncomment AI loop start code in `tata.py`

3. **Test Full Audio Loop**
   - Place test call
   - Verify audio capture and playback
   - Monitor latencies at each stage
   - Test all error paths

4. **Optimize for Production**
   - Tune timeout values based on real-world latencies
   - Implement conversation context trimming for long calls
   - Add caching for common phrases (TTS optimization)
   - Set up comprehensive monitoring

---

### Original "Next Phase" Section (Now Implemented)

The backend infrastructure for AI-powered conversations is now **IMPLEMENTED**:

✅ **Audio Streaming** - ARI client interface ready (audio pipeline TODO)
✅ **Speech-to-Text (STT)** - Whisper integration complete
✅ **Large Language Model (LLM)** - GPT-4 with AIProfile integration complete
✅ **Text-to-Speech (TTS)** - OpenAI TTS integration complete
✅ **Conversation State Management** - Redis-based state tracking complete
⚠️ **Call Disposition** - Update ended_at on completion (TODO in future iteration)

The remaining work is primarily ARI External Media implementation for actual audio flow.

---

### Troubleshooting

#### Call Not Reaching VCA
1. Check Asterisk logs: `tail -f /var/log/asterisk/full`
2. Verify SIP trunk status: `asterisk -rx "pjsip show endpoints"`
3. Test dialplan: `asterisk -rx "dialplan show from-tata-trunk"`
4. Verify VCA endpoint is accessible: `curl http://localhost:8000/internal/telephony/inbound`
5. Check firewall rules: `iptables -L` or `ufw status`

#### DID Not Found Errors
1. Verify DID in database: `SELECT * FROM phone_numbers WHERE did_number = '+15551234567';`
2. Check DID format matches (with/without + prefix)
3. Verify DID is active: `is_active = true`
4. Check VCA backend logs for DID resolution failures

#### Database Connection Errors
1. Verify DATABASE_URL in environment
2. Check PostgreSQL is running: `systemctl status postgresql`
3. Test connection: `psql $DATABASE_URL`
4. Check connection pool exhaustion in logs

#### Asterisk Cannot Reach Tata SIP
1. Verify Tata SIP server IPs are correct in `pjsip.conf`
2. Check network connectivity: `ping TATA_SIP_SERVER_IP`
3. Verify firewall allows UDP/TCP 5060 outbound
4. Check SIP registration: `asterisk -rx "pjsip show registrations"`
5. Review Asterisk SIP logs: `asterisk -rx "pjsip set logger on"`

---

## Original TODO Section
