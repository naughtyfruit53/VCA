/**
 * PricingPage Component - Phase 7
 * 
 * Static pricing page showing Lite/Pro/Growth tiers.
 * No payment code included.
 * 
 * Features:
 * - Display pricing tiers
 * - Feature comparison
 * - No payment processing
 */

'use client';

interface PricingTier {
  name: string;
  price: string;
  priceDetail: string;
  features: string[];
  highlighted?: boolean;
}

export default function PricingPage() {
  const tiers: PricingTier[] = [
    {
      name: 'Lite',
      price: '₹5,000',
      priceDetail: 'per month',
      features: [
        'Up to 500 calls/month',
        '1 phone number',
        'Basic AI receptionist',
        'Email notifications',
        'Standard support',
      ],
    },
    {
      name: 'Pro',
      price: '₹10,000',
      priceDetail: 'per month',
      features: [
        'Up to 2,000 calls/month',
        'Up to 3 phone numbers',
        'Advanced AI receptionist',
        'WhatsApp + Email notifications',
        'Priority support',
        'Call analytics',
      ],
      highlighted: true,
    },
    {
      name: 'Growth',
      price: '₹25,000',
      priceDetail: 'per month',
      features: [
        'Unlimited calls',
        'Unlimited phone numbers',
        'Custom AI profiles',
        'All notification channels',
        'Dedicated support',
        'Advanced analytics',
        'API access',
        'Custom integrations',
      ],
    },
  ];

  return (
    <div className="bg-gray-50 min-h-screen py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600">
            Choose the plan that's right for your business
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {tiers.map((tier) => (
            <div
              key={tier.name}
              className={`bg-white rounded-lg shadow-lg overflow-hidden ${
                tier.highlighted ? 'ring-2 ring-blue-600 transform scale-105' : ''
              }`}
            >
              {tier.highlighted && (
                <div className="bg-blue-600 text-white text-center py-2 text-sm font-semibold">
                  MOST POPULAR
                </div>
              )}
              
              <div className="p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {tier.name}
                </h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-900">
                    {tier.price}
                  </span>
                  <span className="text-gray-600 ml-2">{tier.priceDetail}</span>
                </div>

                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <svg
                        className="w-5 h-5 text-green-500 mr-3 flex-shrink-0 mt-0.5"
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
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors ${
                    tier.highlighted
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  Get Started
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-4">
            All plans include a 14-day free trial. No credit card required.
          </p>
          <p className="text-sm text-gray-500">
            Prices are in Indian Rupees (INR). Custom enterprise plans available
            on request.
          </p>
        </div>

        {/* FAQ Section */}
        <div className="mt-16 bg-white rounded-lg shadow p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Frequently Asked Questions
          </h2>
          <div className="space-y-4">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Can I change plans later?
              </h3>
              <p className="text-gray-600">
                Yes, you can upgrade or downgrade your plan at any time. Changes
                take effect immediately.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                What happens if I exceed my call limit?
              </h3>
              <p className="text-gray-600">
                You'll be notified when you reach 80% of your limit. Additional
                calls are charged at ₹5 per call.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                Is there a setup fee?
              </h3>
              <p className="text-gray-600">
                No setup fees. You only pay your monthly subscription.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
