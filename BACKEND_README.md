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

## TODO

See `main.py` for comprehensive list of planned features:
- Tenant management endpoints
- Phone number management
- Call management
- AI profile management
- Telephony integration
- AI/LLM integration
- Analytics endpoints
- Billing endpoints
- Webhook configuration

All future features must follow strict tenant isolation patterns.
