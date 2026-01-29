# VCA Frontend - Admin Dashboard

A minimal Next.js (App Router) admin frontend for the VCA Voice AI Agent Platform.

## Overview

This is a TypeScript-based Next.js application providing a simple admin interface for managing tenants, phone numbers, and AI profiles. The frontend communicates exclusively with the VCA backend API.

## Technology Stack

- **Framework**: Next.js 15+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React useState/useEffect (no external state libraries)
- **API Communication**: Native fetch API

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Root page (redirects to /tenants)
│   ├── tenants/
│   │   ├── page.tsx        # Tenants list page
│   │   └── [tenant_id]/
│   │       └── page.tsx    # Tenant detail page
│   └── globals.css         # Global styles
├── lib/
│   └── api.ts              # Backend API client
└── package.json
```

## Features & Pages

### 1. Tenants List Page (`/tenants`)

**Features:**
- List all tenants (stored in localStorage)
- Create new tenants with:
  - Status selection (active/suspended/deleted) - defaults to "active"
  - Plan selection (starter/growth/custom) - defaults to "starter"
- Click tenant to view details

**Endpoints Used:**
- `POST /api/tenants` - Create new tenant

### 2. Tenant Detail Page (`/tenants/[tenant_id]`)

**Features:**
- Display tenant information (ID, status, plan, created date)
- Manage phone numbers:
  - List all phone numbers attached to tenant
  - Attach new phone numbers (DID format)
  - Provider type fixed to "generic"
- Manage AI profiles:
  - List all AI profiles for tenant
  - Create new AI profiles with:
    - Role selector (receptionist/sales/support/dispatcher/custom)
    - System prompt textarea (required, min 1 character)
    - Default toggle with warning logic
  - Edit existing AI profiles
  - Warning displayed if multiple profiles are marked as default

**Endpoints Used:**
- `GET /api/tenants/{tenant_id}` - Get tenant details
- `GET /api/tenants/{tenant_id}/phone-numbers` - List phone numbers
- `POST /api/tenants/{tenant_id}/phone-numbers` - Attach phone number
- `GET /api/tenants/{tenant_id}/ai-profiles` - List AI profiles
- `POST /api/tenants/{tenant_id}/ai-profiles` - Create AI profile
- `PATCH /api/tenants/{tenant_id}/ai-profiles/{ai_profile_id}` - Update AI profile

## Backend API Endpoints

All API endpoints are defined in `/lib/api.ts`:

### Tenant Endpoints
- `POST /api/tenants` - Create tenant
- `GET /api/tenants/{tenant_id}` - Get tenant details
- `PATCH /api/tenants/{tenant_id}` - Update tenant

### Phone Number Endpoints
- `POST /api/tenants/{tenant_id}/phone-numbers` - Attach phone number
- `GET /api/tenants/{tenant_id}/phone-numbers` - List phone numbers
- `PATCH /api/tenants/{tenant_id}/phone-numbers/{phone_number_id}` - Update phone number

### AI Profile Endpoints
- `POST /api/tenants/{tenant_id}/ai-profiles` - Create AI profile
- `GET /api/tenants/{tenant_id}/ai-profiles` - List AI profiles
- `PATCH /api/tenants/{tenant_id}/ai-profiles/{ai_profile_id}` - Update AI profile

## API Client (`lib/api.ts`)

The API client provides typed functions for all backend endpoints:

**Error Handling:**
- All API errors trigger browser alerts with error messages
- Errors are extracted from response.data.detail when available
- Generic fallback messages for network/unknown errors

**Configuration:**
- API base URL: `process.env.NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`)

## Setup & Development

### Prerequisites
- Node.js 18+ 
- npm or yarn
- VCA backend running on http://localhost:8000

### Installation

```bash
cd frontend
npm install
```

### Environment Variables

Create `.env.local` in the frontend directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development Server

```bash
npm run dev
```

The app will be available at http://localhost:3000

### Build for Production

```bash
npm run build
npm start
```

## Design Principles

### Minimal Code
- No complex state management libraries
- No client-side business logic
- Direct API calls with basic error handling
- Simple component structure

### Error Handling
- Basic `alert()` dialogs for all errors
- Errors displayed to user immediately
- No retry logic or complex error states

### No Validation Beyond Backend
- Frontend only validates required fields (HTML5)
- All business logic validation happens in backend API
- Frontend displays backend validation errors via alerts

### AI Profile Warnings
- Visual warning if multiple AI profiles are marked as default
- Warning shown in form when setting a profile as default
- Clear indication of current default profile

## Limitations & Future TODOs

### Current Limitations
- No authentication/authorization
- No pagination (lists all records)
- No search/filter functionality
- No delete operations for resources
- Tenant list stored in localStorage (not from backend)
- No real-time updates
- No loading indicators (basic text only)

### Future Enhancements (TODO)
- User authentication and role-based access
- Pagination for large lists
- Search and filter capabilities
- Delete/archive operations
- Real-time updates via WebSockets
- Better loading states and spinners
- Form validation with helpful hints
- Dark mode support
- Responsive mobile design improvements
- API response caching
- Error boundary components
- Unit and integration tests

## Security Notes

- No sensitive data stored in localStorage
- All authentication will be handled by backend (TODO)
- No client-side secrets or API keys
- HTTPS should be used in production
- CORS must be configured on backend

## Troubleshooting

### "Cannot connect to backend"
- Ensure backend is running on http://localhost:8000
- Check `NEXT_PUBLIC_API_URL` environment variable
- Verify CORS settings on backend allow frontend origin

### "Phone number already exists"
- Each phone number (DID) must be globally unique
- Error message will be displayed via alert

### "Multiple default AI profiles warning"
- Only one AI profile per tenant should be marked as default
- Setting a new default will automatically unset others
- Warning is informational only, not blocking

## Contributing

When adding new features:
1. Keep code minimal and readable
2. Use backend APIs exclusively
3. Handle errors with basic alerts
4. Update this README with new endpoints/features
5. Maintain consistent styling with existing pages
