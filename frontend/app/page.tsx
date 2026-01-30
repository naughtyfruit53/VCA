import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            VCA Platform
          </h1>
          <p className="text-xl text-gray-600">
            Voice AI Agent Platform - Multi-Tenant SaaS
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <Link
            href="/tenants"
            className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Manage Tenants
            </h2>
            <p className="text-gray-600">
              View and manage tenant accounts
            </p>
          </Link>

          <Link
            href="/onboarding"
            className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Onboarding
            </h2>
            <p className="text-gray-600">
              Complete your onboarding checklist
            </p>
          </Link>

          <Link
            href="/demo"
            className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Demo Number
            </h2>
            <p className="text-gray-600">
              Test with a demo phone number
            </p>
          </Link>

          <Link
            href="/pricing"
            className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Pricing
            </h2>
            <p className="text-gray-600">
              View our pricing plans
            </p>
          </Link>
        </div>

        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500">
            Phase 5, 6, and 7 Implementation Complete
          </p>
        </div>
      </div>
    </div>
  );
}
