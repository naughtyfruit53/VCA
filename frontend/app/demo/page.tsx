/**
 * Demo Number Page Route - Phase 7
 */
'use client';

import DemoNumberPage from '@/components/DemoNumberPage';
import ProtectedRoute from '@/components/ProtectedRoute';
import Header from '@/components/Header';

export default function DemoRoute() {
  return (
    <ProtectedRoute>
      <Header />
      <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <DemoNumberPage />
      </div>
    </div>
    </ProtectedRoute>
  );
}
