/**
 * SandboxTester Component - Phase 7
 * 
 * Reuses the simulate API to allow tenants to test their AI agent
 * in a sandbox environment.
 * 
 * Features:
 * - Test inbound call flow
 * - View AI responses
 * - No real calls made
 */

'use client';

import { useState } from 'react';

interface SandboxTesterProps {
  tenantId: string;
}

export default function SandboxTester({ tenantId }: SandboxTesterProps) {
  const [testing, setTesting] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testResults, setTestResults] = useState<string[]>([]);

  const runTest = async () => {
    if (!testInput.trim()) {
      alert('Please enter a test message');
      return;
    }

    setTesting(true);
    
    try {
      // TODO: Replace with actual simulate API call
      // For now, simulate a response
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockResponse = `AI Response: Thank you for testing. Your message was: "${testInput}"`;
      setTestResults([...testResults, `User: ${testInput}`, mockResponse]);
      setTestInput('');
      
    } catch (error) {
      alert('Test failed. Please try again.');
    } finally {
      setTesting(false);
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-2">Sandbox Tester</h2>
      <p className="text-gray-600 mb-4">
        Test your AI agent without making real calls
      </p>

      {/* Test Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Test Message
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && runTest()}
            placeholder="Enter a test message..."
            className="flex-1 px-3 py-2 border rounded"
            disabled={testing}
          />
          <button
            onClick={runTest}
            disabled={testing}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Send'}
          </button>
        </div>
      </div>

      {/* Test Results */}
      {testResults.length > 0 && (
        <div className="mb-4">
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm font-medium">
              Test Results
            </label>
            <button
              onClick={clearResults}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Clear
            </button>
          </div>
          <div className="border rounded p-4 bg-gray-50 max-h-96 overflow-y-auto">
            <div className="space-y-2">
              {testResults.map((result, index) => (
                <div
                  key={index}
                  className={`p-3 rounded ${
                    result.startsWith('User:')
                      ? 'bg-blue-100 text-blue-900'
                      : 'bg-green-100 text-green-900'
                  }`}
                >
                  <p className="text-sm font-mono">{result}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Info Box */}
      <div className="p-4 bg-blue-50 border border-blue-200 rounded">
        <p className="text-sm text-blue-800">
          <strong>Note:</strong> This is a sandbox environment. No real calls
          are made, and no charges are incurred.
        </p>
      </div>
    </div>
  );
}
