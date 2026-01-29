/**
 * API client for VCA backend.
 * 
 * Provides functions to interact with backend API endpoints.
 * All error handling uses basic alerts as specified in requirements.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Handle API errors with basic alerts.
 */
function handleError(error: any, defaultMessage: string): void {
  const message = error.response?.data?.detail || error.message || defaultMessage;
  alert(`Error: ${message}`);
  throw error;
}

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw { response: { data: error }, message: error.detail };
    }

    return response.json();
  } catch (error) {
    handleError(error, 'An error occurred');
    throw error;
  }
}

// ============================================================================
// Tenant API
// ============================================================================

export interface Tenant {
  id: string;
  status: 'active' | 'suspended' | 'deleted';
  plan: 'starter' | 'growth' | 'custom';
  created_at: string;
  updated_at: string;
}

export interface TenantCreate {
  status?: 'active' | 'suspended' | 'deleted';
  plan?: 'starter' | 'growth' | 'custom';
}

export interface TenantUpdate {
  status?: 'active' | 'suspended' | 'deleted';
  plan?: 'starter' | 'growth' | 'custom';
}

export async function createTenant(data: TenantCreate): Promise<Tenant> {
  return apiFetch<Tenant>('/api/tenants', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getTenant(tenantId: string): Promise<Tenant> {
  return apiFetch<Tenant>(`/api/tenants/${tenantId}`);
}

export async function updateTenant(tenantId: string, data: TenantUpdate): Promise<Tenant> {
  return apiFetch<Tenant>(`/api/tenants/${tenantId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// Phone Number API
// ============================================================================

export interface PhoneNumber {
  id: string;
  tenant_id: string;
  did_number: string;
  provider_type: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PhoneNumberCreate {
  did_number: string;
  provider_type: string;
  is_active?: boolean;
}

export interface PhoneNumberUpdate {
  provider_type?: string;
  is_active?: boolean;
}

export async function createPhoneNumber(tenantId: string, data: PhoneNumberCreate): Promise<PhoneNumber> {
  return apiFetch<PhoneNumber>(`/api/tenants/${tenantId}/phone-numbers`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listPhoneNumbers(tenantId: string): Promise<PhoneNumber[]> {
  return apiFetch<PhoneNumber[]>(`/api/tenants/${tenantId}/phone-numbers`);
}

export async function updatePhoneNumber(
  tenantId: string,
  phoneNumberId: string,
  data: PhoneNumberUpdate
): Promise<PhoneNumber> {
  return apiFetch<PhoneNumber>(`/api/tenants/${tenantId}/phone-numbers/${phoneNumberId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

// ============================================================================
// AI Profile API
// ============================================================================

export interface AIProfile {
  id: string;
  tenant_id: string;
  role: 'receptionist' | 'sales' | 'support' | 'dispatcher' | 'custom';
  system_prompt: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface AIProfileCreate {
  role?: 'receptionist' | 'sales' | 'support' | 'dispatcher' | 'custom';
  system_prompt: string;
  is_default?: boolean;
}

export interface AIProfileUpdate {
  role?: 'receptionist' | 'sales' | 'support' | 'dispatcher' | 'custom';
  system_prompt?: string;
  is_default?: boolean;
}

export async function createAIProfile(tenantId: string, data: AIProfileCreate): Promise<AIProfile> {
  return apiFetch<AIProfile>(`/api/tenants/${tenantId}/ai-profiles`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function listAIProfiles(tenantId: string): Promise<AIProfile[]> {
  return apiFetch<AIProfile[]>(`/api/tenants/${tenantId}/ai-profiles`);
}

export async function updateAIProfile(
  tenantId: string,
  aiProfileId: string,
  data: AIProfileUpdate
): Promise<AIProfile> {
  return apiFetch<AIProfile>(`/api/tenants/${tenantId}/ai-profiles/${aiProfileId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}
