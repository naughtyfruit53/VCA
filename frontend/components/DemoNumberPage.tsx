/**
 * DemoNumberPage Component - Phase 7
 * 
 * Shows demo DID/number with prominent warning banner.
 * 
 * Features:
 * - Display demo phone number
 * - Prominent "NOT FOR PRODUCTION" warning
 * - Clear visual indicators
 */

'use client';

export default function DemoNumberPage() {
  const demoNumber = '+91 98765 43210'; // Example demo number

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Warning Banner */}
      <div className="mb-6 p-4 bg-red-50 border-2 border-red-500 rounded">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <svg
              className="h-6 w-6 text-red-600"
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
          <div className="ml-3">
            <h3 className="text-lg font-bold text-red-800">
              ⚠️ NOT FOR PRODUCTION
            </h3>
            <p className="mt-1 text-sm text-red-700">
              This is a demo number for testing purposes only. Do NOT use this
              number for real customer calls. It may be shared with other users
              and is not secure.
            </p>
          </div>
        </div>
      </div>

      <h2 className="text-2xl font-bold mb-2">Demo Phone Number</h2>
      <p className="text-gray-600 mb-6">
        Use this number to test your AI agent in a safe environment
      </p>

      {/* Demo Number Display */}
      <div className="p-6 bg-gray-50 border-2 border-dashed border-gray-300 rounded text-center">
        <p className="text-sm text-gray-600 mb-2">Demo Number</p>
        <p className="text-4xl font-bold text-gray-900 mb-2">{demoNumber}</p>
        <p className="text-sm text-gray-500">
          (Demo only - shared with other test users)
        </p>
      </div>

      {/* Usage Instructions */}
      <div className="mt-6">
        <h3 className="font-semibold mb-3">How to Use</h3>
        <ol className="list-decimal list-inside space-y-2 text-sm text-gray-700">
          <li>Call the demo number from your phone</li>
          <li>Test your AI agent's responses</li>
          <li>Verify the conversation flow</li>
          <li>Once satisfied, proceed to add your own production number</li>
        </ol>
      </div>

      {/* Additional Warnings */}
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <h4 className="font-semibold text-yellow-900 mb-2">Important Notes:</h4>
        <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800">
          <li>Demo numbers may be reset periodically</li>
          <li>Call recordings are not saved in demo mode</li>
          <li>Test data may be deleted without notice</li>
          <li>For production use, add your own phone number</li>
        </ul>
      </div>
    </div>
  );
}
