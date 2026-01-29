'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  getTenant,
  listPhoneNumbers,
  createPhoneNumber,
  listAIProfiles,
  createAIProfile,
  updateAIProfile,
  type Tenant,
  type PhoneNumber,
  type AIProfile,
  type PhoneNumberCreate,
  type AIProfileCreate,
} from '@/lib/api';

export default function TenantDetailPage() {
  const params = useParams();
  const router = useRouter();
  const tenantId = params.tenant_id as string;

  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([]);
  const [aiProfiles, setAIProfiles] = useState<AIProfile[]>([]);
  const [loading, setLoading] = useState(true);

  // Phone number form
  const [showPhoneForm, setShowPhoneForm] = useState(false);
  const [phoneFormData, setPhoneFormData] = useState<PhoneNumberCreate>({
    did_number: '',
    provider_type: 'generic',
    is_active: true,
  });

  // AI Profile form
  const [showAIForm, setShowAIForm] = useState(false);
  const [editingProfile, setEditingProfile] = useState<AIProfile | null>(null);
  const [aiFormData, setAIFormData] = useState<AIProfileCreate>({
    role: 'receptionist',
    system_prompt: '',
    is_default: false,
  });

  useEffect(() => {
    loadData();
  }, [tenantId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tenantData, phones, profiles] = await Promise.all([
        getTenant(tenantId),
        listPhoneNumbers(tenantId),
        listAIProfiles(tenantId),
      ]);
      setTenant(tenantData);
      setPhoneNumbers(phones);
      setAIProfiles(profiles);
    } catch (error) {
      // Error handled by API client
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePhone = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPhoneNumber(tenantId, phoneFormData);
      setPhoneFormData({ did_number: '', provider_type: 'generic', is_active: true });
      setShowPhoneForm(false);
      loadData();
      alert('Phone number added successfully!');
    } catch (error) {
      // Error handled by API client
    }
  };

  const handleCreateOrUpdateAI = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingProfile) {
        await updateAIProfile(tenantId, editingProfile.id, aiFormData);
        alert('AI Profile updated successfully!');
      } else {
        await createAIProfile(tenantId, aiFormData);
        alert('AI Profile created successfully!');
      }
      setAIFormData({ role: 'receptionist', system_prompt: '', is_default: false });
      setShowAIForm(false);
      setEditingProfile(null);
      loadData();
    } catch (error) {
      // Error handled by API client
    }
  };

  const handleEditProfile = (profile: AIProfile) => {
    setEditingProfile(profile);
    setAIFormData({
      role: profile.role,
      system_prompt: profile.system_prompt,
      is_default: profile.is_default,
    });
    setShowAIForm(true);
  };

  const defaultProfileCount = aiProfiles.filter(p => p.is_default).length;

  if (loading) {
    return <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center">
      <p>Loading...</p>
    </div>;
  }

  if (!tenant) {
    return <div className="min-h-screen bg-gray-50 p-8 flex items-center justify-center">
      <p>Tenant not found</p>
    </div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <button
            onClick={() => router.push('/tenants')}
            className="mb-4 text-blue-600 hover:underline"
          >
            ← Back to Tenants
          </button>
          <h1 className="text-2xl font-bold mb-4">Tenant Details</h1>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-600">ID</p>
              <p className="font-medium">{tenant.id}</p>
            </div>
            <div>
              <p className="text-gray-600">Status</p>
              <p className="font-medium">{tenant.status}</p>
            </div>
            <div>
              <p className="text-gray-600">Plan</p>
              <p className="font-medium">{tenant.plan}</p>
            </div>
            <div>
              <p className="text-gray-600">Created</p>
              <p className="font-medium">{new Date(tenant.created_at).toLocaleString()}</p>
            </div>
          </div>
        </div>

        {/* Phone Numbers */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Phone Numbers</h2>
            <button
              onClick={() => setShowPhoneForm(!showPhoneForm)}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {showPhoneForm ? 'Cancel' : 'Attach Number'}
            </button>
          </div>

          {showPhoneForm && (
            <form onSubmit={handleCreatePhone} className="mb-4 p-4 border rounded">
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Phone Number (DID)</label>
                <input
                  type="text"
                  value={phoneFormData.did_number}
                  onChange={(e) => setPhoneFormData({ ...phoneFormData, did_number: e.target.value })}
                  placeholder="+15551234567"
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
              >
                Add Number
              </button>
            </form>
          )}

          <div className="space-y-2">
            {phoneNumbers.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No phone numbers attached</p>
            ) : (
              phoneNumbers.map((phone) => (
                <div key={phone.id} className="p-3 border rounded">
                  <p className="font-medium">{phone.did_number}</p>
                  <p className="text-sm text-gray-600">
                    Provider: {phone.provider_type} | 
                    Status: {phone.is_active ? 'Active' : 'Inactive'}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI Profiles */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">AI Profiles</h2>
            <button
              onClick={() => {
                setEditingProfile(null);
                setAIFormData({ role: 'receptionist', system_prompt: '', is_default: false });
                setShowAIForm(!showAIForm);
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              {showAIForm && !editingProfile ? 'Cancel' : 'Create Profile'}
            </button>
          </div>

          {defaultProfileCount > 1 && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-300 rounded">
              <p className="text-yellow-800 font-medium">⚠️ Warning: Multiple default AI profiles detected!</p>
              <p className="text-sm text-yellow-700">Only one profile should be marked as default.</p>
            </div>
          )}

          {showAIForm && (
            <form onSubmit={handleCreateOrUpdateAI} className="mb-4 p-4 border rounded">
              <h3 className="text-lg font-semibold mb-4">
                {editingProfile ? 'Edit AI Profile' : 'Create AI Profile'}
              </h3>
              
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">Role</label>
                <select
                  value={aiFormData.role}
                  onChange={(e) => setAIFormData({ ...aiFormData, role: e.target.value as any })}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="receptionist">Receptionist</option>
                  <option value="sales">Sales</option>
                  <option value="support">Support</option>
                  <option value="dispatcher">Dispatcher</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">System Prompt</label>
                <textarea
                  value={aiFormData.system_prompt}
                  onChange={(e) => setAIFormData({ ...aiFormData, system_prompt: e.target.value })}
                  placeholder="Enter system prompt for AI..."
                  className="w-full px-3 py-2 border rounded h-32"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={aiFormData.is_default}
                    onChange={(e) => setAIFormData({ ...aiFormData, is_default: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium">Set as default profile</span>
                </label>
                {aiFormData.is_default && defaultProfileCount > 0 && (
                  <p className="text-sm text-yellow-700 mt-1">
                    ⚠️ This will unset the current default profile
                  </p>
                )}
              </div>

              <div className="flex gap-2">
                <button
                  type="submit"
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  {editingProfile ? 'Update' : 'Create'}
                </button>
                {editingProfile && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingProfile(null);
                      setShowAIForm(false);
                      setAIFormData({ role: 'receptionist', system_prompt: '', is_default: false });
                    }}
                    className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
                  >
                    Cancel Edit
                  </button>
                )}
              </div>
            </form>
          )}

          <div className="space-y-2">
            {aiProfiles.length === 0 ? (
              <p className="text-gray-500 text-center py-4">No AI profiles created</p>
            ) : (
              aiProfiles.map((profile) => (
                <div key={profile.id} className="p-3 border rounded">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium">
                        {profile.role}
                        {profile.is_default && (
                          <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            DEFAULT
                          </span>
                        )}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {profile.system_prompt.length > 100
                          ? `${profile.system_prompt.substring(0, 100)}...`
                          : profile.system_prompt}
                      </p>
                    </div>
                    <button
                      onClick={() => handleEditProfile(profile)}
                      className="ml-2 px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
                    >
                      Edit
                    </button>
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
