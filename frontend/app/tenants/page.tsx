'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createTenant, type Tenant, type TenantCreate } from '@/lib/api';

export default function TenantsPage() {
  const router = useRouter();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState<TenantCreate>({
    status: 'active',
    plan: 'starter',
  });

  // Load tenants from localStorage (simple storage for demo)
  useEffect(() => {
    const stored = localStorage.getItem('tenants');
    if (stored) {
      setTenants(JSON.parse(stored));
    }
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const newTenant = await createTenant(formData);
      const updatedTenants = [...tenants, newTenant];
      setTenants(updatedTenants);
      localStorage.setItem('tenants', JSON.stringify(updatedTenants));
      setFormData({ status: 'active', plan: 'starter' });
      setCreating(false);
      alert('Tenant created successfully!');
    } catch (error) {
      // Error already handled by API client
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-bold">Tenants</h1>
            <button
              onClick={() => setCreating(!creating)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {creating ? 'Cancel' : 'Create Tenant'}
            </button>
          </div>

          {creating && (
            <form onSubmit={handleCreate} className="mb-6 p-4 border rounded">
              <h2 className="text-lg font-semibold mb-4">Create New Tenant</h2>
              
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="deleted">Deleted</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Plan</label>
                <select
                  value={formData.plan}
                  onChange={(e) => setFormData({ ...formData, plan: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="starter">Starter</option>
                  <option value="growth">Growth</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create'}
              </button>
            </form>
          )}

          <div className="space-y-4">
            {tenants.length === 0 ? (
              <p className="text-gray-500 text-center py-8">No tenants yet. Create one to get started.</p>
            ) : (
              tenants.map((tenant) => (
                <div
                  key={tenant.id}
                  onClick={() => router.push(`/tenants/${tenant.id}`)}
                  className="p-4 border rounded hover:bg-gray-50 cursor-pointer"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Tenant ID: {tenant.id}</p>
                      <p className="text-sm text-gray-600">
                        Status: <span className="font-medium">{tenant.status}</span> | 
                        Plan: <span className="font-medium">{tenant.plan}</span>
                      </p>
                      <p className="text-xs text-gray-500">
                        Created: {new Date(tenant.created_at).toLocaleString()}
                      </p>
                    </div>
                    <svg 
                      className="w-5 h-5 text-gray-400" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
