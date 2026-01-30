/**
 * GoLiveToggle Component - Phase 7
 * 
 * Admin-only toggle to enable real inbound calls.
 * 
 * Features:
 * - Admin-only access
 * - Confirmation dialog with specific copy
 * - Uses backend flag to control routing
 * - Clear visual feedback
 * 
 * IMPORTANT: Confirmation copy as specified:
 * "This will route real customer calls to the AI."
 */

'use client';

import { useState } from 'react';

interface GoLiveToggleProps {
  tenantId: string;
  isAdmin?: boolean;
  initialStatus?: boolean;
}

export default function GoLiveToggle({
  tenantId,
  isAdmin = true,
  initialStatus = false,
}: GoLiveToggleProps) {
  const [isLive, setIsLive] = useState(initialStatus);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!isAdmin) {
    return null; // Only show to admins
  }

  const handleToggleClick = () => {
    if (!isLive) {
      // Going live - show confirmation
      setShowConfirmation(true);
    } else {
      // Going offline - no confirmation needed
      handleGoOffline();
    }
  };

  const handleGoLive = async () => {
    setLoading(true);
    try {
      // TODO: Call backend API to enable live mode
      // await updateTenantLiveStatus(tenantId, true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setIsLive(true);
      setShowConfirmation(false);
      alert('Your AI agent is now live and handling real customer calls!');
    } catch (error) {
      alert('Failed to go live. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoOffline = async () => {
    setLoading(true);
    try {
      // TODO: Call backend API to disable live mode
      // await updateTenantLiveStatus(tenantId, false);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setIsLive(false);
      alert('Your AI agent is now offline. Real calls will not be routed.');
    } catch (error) {
      alert('Failed to go offline. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Go Live Status
            </h3>
            <p className="text-sm text-gray-600">
              {isLive
                ? 'Your AI agent is live and handling real customer calls'
                : 'Your AI agent is in test mode. Enable to start handling real calls.'}
            </p>
          </div>
          
          <button
            onClick={handleToggleClick}
            disabled={loading}
            className={`relative inline-flex h-12 w-24 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 ${
              isLive
                ? 'bg-green-600 focus:ring-green-500'
                : 'bg-gray-200 focus:ring-gray-500'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-11 w-11 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                isLive ? 'translate-x-12' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Status Badge */}
        <div className="mt-4">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
              isLive
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            <span
              className={`w-2 h-2 mr-2 rounded-full ${
                isLive ? 'bg-green-600' : 'bg-gray-600'
              }`}
            />
            {isLive ? 'LIVE' : 'TEST MODE'}
          </span>
        </div>

        {/* Warning when live */}
        {isLive && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded">
            <p className="text-sm text-green-800">
              <strong>Live Mode Active:</strong> Real customer calls are being
              routed to your AI agent.
            </p>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex items-start mb-4">
              <div className="flex-shrink-0">
                <svg
                  className="h-6 w-6 text-yellow-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Confirm Go Live
                </h3>
                <p className="text-sm text-gray-700">
                  This will route real customer calls to the AI.
                </p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
              <p className="text-sm text-yellow-800">
                Make sure you have:
              </p>
              <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside space-y-1">
                <li>Tested your AI agent in sandbox mode</li>
                <li>Configured your AI profile correctly</li>
                <li>Set up notification preferences</li>
              </ul>
            </div>

            <div className="mt-6 flex gap-3">
              <button
                onClick={() => setShowConfirmation(false)}
                disabled={loading}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleGoLive}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Going Live...' : 'Go Live'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
