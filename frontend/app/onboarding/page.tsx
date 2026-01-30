/**
 * Onboarding Page - Phase 7
 * 
 * Shows onboarding checklist for a tenant
 */

import OnboardingChecklist from '@/components/OnboardingChecklist';

export default function OnboardingPage() {
  // In a real app, this would get tenant ID from auth/session
  const mockTenantId = 'demo-tenant-123';

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <OnboardingChecklist tenantId={mockTenantId} />
      </div>
    </div>
  );
}
