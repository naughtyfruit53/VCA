/**
 * OnboardingChecklist Component - Phase 7
 * 
 * Multi-step onboarding checklist showing progress per tenant.
 * 
 * Features:
 * - Shows onboarding steps with completion status
 * - Multi-step progress tracking
 * - Tenant-scoped
 */

'use client';

import { useState, useEffect } from 'react';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

interface OnboardingChecklistProps {
  tenantId: string;
}

export default function OnboardingChecklist({ tenantId }: OnboardingChecklistProps) {
  const [steps, setSteps] = useState<OnboardingStep[]>([
    {
      id: 'create_tenant',
      title: 'Create Tenant Account',
      description: 'Set up your organization account',
      completed: true, // Always true if viewing this
    },
    {
      id: 'add_phone',
      title: 'Add Phone Number',
      description: 'Register a DID number for inbound calls',
      completed: false,
    },
    {
      id: 'configure_ai',
      title: 'Configure AI Profile',
      description: 'Set up your AI receptionist behavior',
      completed: false,
    },
    {
      id: 'test_sandbox',
      title: 'Test in Sandbox',
      description: 'Try out your AI agent in sandbox mode',
      completed: false,
    },
    {
      id: 'go_live',
      title: 'Go Live',
      description: 'Enable real customer calls',
      completed: false,
    },
  ]);

  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Calculate progress
    const completedCount = steps.filter(step => step.completed).length;
    const progressPercent = (completedCount / steps.length) * 100;
    setProgress(progressPercent);

    // Load completion status from localStorage (simple demo)
    const savedStatus = localStorage.getItem(`onboarding_${tenantId}`);
    if (savedStatus) {
      const parsed = JSON.parse(savedStatus);
      setSteps(parsed);
    }
  }, [tenantId]);

  const toggleStep = (stepId: string) => {
    const updatedSteps = steps.map(step => {
      if (step.id === stepId) {
        return { ...step, completed: !step.completed };
      }
      return step;
    });
    setSteps(updatedSteps);
    localStorage.setItem(`onboarding_${tenantId}`, JSON.stringify(updatedSteps));
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-2xl font-bold mb-2">Onboarding Checklist</h2>
      <p className="text-gray-600 mb-4">Complete these steps to get started</p>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium">Progress</span>
          <span className="text-sm font-medium">{Math.round(progress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-4">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className="flex items-start p-4 border rounded hover:bg-gray-50 cursor-pointer"
            onClick={() => toggleStep(step.id)}
          >
            <div className="flex-shrink-0 mt-1">
              {step.completed ? (
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                  <svg
                    className="w-4 h-4 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              ) : (
                <div className="w-6 h-6 border-2 border-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-xs text-gray-400">{index + 1}</span>
                </div>
              )}
            </div>
            <div className="ml-4 flex-1">
              <h3 className={`font-medium ${step.completed ? 'text-gray-500 line-through' : 'text-gray-900'}`}>
                {step.title}
              </h3>
              <p className="text-sm text-gray-600 mt-1">{step.description}</p>
            </div>
          </div>
        ))}
      </div>

      {progress === 100 && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded">
          <p className="text-green-800 font-medium">
            🎉 Congratulations! You've completed onboarding.
          </p>
        </div>
      )}
    </div>
  );
}
