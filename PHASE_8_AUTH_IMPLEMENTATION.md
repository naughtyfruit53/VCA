# Phase 8: Authentication Implementation

This document describes the authentication system implemented in Phase 8, including user identity binding, JWT verification, and tenant-scoped dashboards.

## Overview

Phase 8 implements a complete authentication system using Supabase for user management and JWT token verification. All API endpoints are now protected and require valid authentication tokens. The frontend provides login, signup, and OAuth flows with protected dashboard routes.

## Backend Changes

### 1. User Model

A new `users` table has been added to the database with the following schema:

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  supabase_user_id UUID UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  display_name VARCHAR(255),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL DEFAULT 'member',  -- 'owner', 'admin', 'member'
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

**Migration**: Run `alembic upgrade head` to apply the migration.

### 2. Authentication Service

Located in `app/services/auth.py`, provides:

- **JWT Verification**: Verifies Supabase JWT tokens using HS256 algorithm
- **JWK Caching**: Caches JWT verification keys to improve performance
- **User Lookup**: Maps Supabase user IDs to internal user records
- **DEV_AUTH_BYPASS**: Optional development mode bypass (default: OFF)

### 3. Protected Endpoints

All tenant-scoped API endpoints now require authentication:

- **Tenant API** (`/api/tenants/*`): Requires user to belong to the tenant
- **Phone Number API** (`/api/tenants/{id}/phone-numbers`): Owner/admin only for create/update
- **AI Profile API** (`/api/tenants/{id}/ai-profiles`): Owner/admin only for create/update
- **Agent Config API** (`/api/tenants/{id}/agent-config`): Owner/admin only for updates

### 4. New Endpoints

- **GET `/api/me`**: Returns current user's tenant information

### 5. Environment Variables

Add to your `.env` file:

```bash
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your_supabase_jwt_secret_here

# Development Auth Bypass (OPTIONAL - default OFF)
# WARNING: Only enable in development environments
DEV_AUTH_BYPASS=false
```

## Frontend Changes

### 1. Authentication Context

The `AuthProvider` component (`frontend/contexts/AuthContext.tsx`) provides:

- User state management
- Login/signup/logout methods
- Session refresh
- Google OAuth support
- Error handling

### 2. Protected Routes

All dashboard pages are now wrapped with `ProtectedRoute`:

- Redirects to `/login` if not authenticated
- Shows loading state during auth check
- Allows access only to authenticated users

### 3. New Pages

- **`/login`**: Email/password and Google OAuth login
- **`/signup`**: User registration with email verification
- **`/auth/callback`**: OAuth callback handler

### 4. Header Component

All authenticated pages now include a header showing:

- Logged-in user email
- Logout button

### 5. API Client Updates

The API client (`frontend/lib/api.ts`) now:

- Automatically includes `Authorization: Bearer <token>` header
- Extracts token from Supabase session
- Handles 401 errors

### 6. Environment Variables

Create `frontend/.env.local` with:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Setup Instructions

### Backend Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Supabase credentials
   ```

3. **Run Migration**:
   ```bash
   alembic upgrade head
   ```

4. **Create Initial User** (after Supabase setup):
   ```python
   # In Python shell or script
   from app.config.database import SessionLocal
   from app.models import User, Tenant
   from uuid import uuid4
   
   db = SessionLocal()
   
   # Create tenant
   tenant = Tenant(
       status='active',
       plan='starter',
       primary_language='en'
   )
   db.add(tenant)
   db.commit()
   
   # Create user (use your Supabase user ID)
   user = User(
       supabase_user_id='<your-supabase-user-id>',
       email='your@email.com',
       tenant_id=tenant.id,
       role='owner'
   )
   db.add(user)
   db.commit()
   ```

5. **Start Backend**:
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local and add your Supabase credentials
   ```

3. **Start Frontend**:
   ```bash
   npm run dev
   ```

### Supabase Setup

1. **Create Project**: Create a new project at [supabase.com](https://supabase.com)

2. **Enable Email Auth**:
   - Go to Authentication > Providers
   - Enable Email provider
   - Configure email templates

3. **Enable Google OAuth** (optional):
   - Go to Authentication > Providers
   - Enable Google provider
   - Add OAuth credentials from Google Cloud Console
   - Add authorized redirect URIs: `https://your-project.supabase.co/auth/v1/callback`

4. **Get Credentials**:
   - Project URL: Settings > API > Project URL
   - Anon Key: Settings > API > Project API keys > anon/public
   - JWT Secret: Settings > API > JWT Settings > JWT Secret

## Testing

### Manual Testing

1. **Registration**:
   - Visit `/signup`
   - Register with email and password
   - Check email for verification link
   - Verify email
   - Create user record in backend database

2. **Login**:
   - Visit `/login`
   - Login with verified credentials
   - Should redirect to home page
   - Header should show user email

3. **Protected Routes**:
   - Try accessing `/tenants` without login
   - Should redirect to `/login`
   - After login, should access successfully

4. **API Authentication**:
   - Make API calls from frontend
   - Should include Authorization header
   - Backend should verify token and allow access

5. **Logout**:
   - Click logout button in header
   - Should clear session and redirect to home
   - Protected routes should now be inaccessible

### DEV_AUTH_BYPASS Mode

For development/testing without Supabase:

1. Set `DEV_AUTH_BYPASS=true` in backend `.env`
2. Create a test user in the database
3. Backend will use the first user found for all requests
4. **WARNING**: Never enable this in production!

## Security Considerations

1. **JWT Secret**: Keep `SUPABASE_JWT_SECRET` secure and never commit to version control

2. **DEV_AUTH_BYPASS**: Only enable in local development, never in production

3. **HTTPS**: Always use HTTPS in production for API calls

4. **Token Expiration**: Supabase tokens expire after 1 hour by default

5. **Tenant Isolation**: All API endpoints enforce tenant boundaries

6. **Role-Based Access**: Create/update operations require owner or admin role

## Troubleshooting

### Backend Issues

**401 Unauthorized**:
- Check that `SUPABASE_JWT_SECRET` matches your Supabase project
- Verify token is being sent in Authorization header
- Check token hasn't expired

**User not found**:
- Create user record in database with matching `supabase_user_id`
- Verify `supabase_user_id` matches the `sub` claim in JWT

**403 Forbidden**:
- User's `tenant_id` doesn't match the resource
- User doesn't have required role (owner/admin)

### Frontend Issues

**Redirect loop**:
- Clear browser cookies and local storage
- Check Supabase session is being stored correctly

**CORS errors**:
- Verify `NEXT_PUBLIC_API_URL` is correct
- Add CORS middleware to backend if needed

**OAuth not working**:
- Verify redirect URIs in Supabase and OAuth provider
- Check callback page at `/auth/callback`

## Migration from Previous Phases

If you have existing tenants and need to add authentication:

1. Set up Supabase and configure environment variables
2. Run the users table migration
3. For each existing tenant, create an owner user:
   ```python
   # Create owner user for existing tenant
   user = User(
       supabase_user_id='<supabase-user-id>',
       email='owner@example.com',
       tenant_id='<existing-tenant-id>',
       role='owner'
   )
   db.add(user)
   db.commit()
   ```
4. Users can then login and access their tenant's data

## Next Steps

Future enhancements to consider:

- Email verification enforcement
- Password reset flow
- Multi-factor authentication
- User invitation system
- Role management UI
- Audit logging for user actions
- Session management (view/revoke active sessions)
