'use client'

import { ProductData, MockDataSummary, FormData } from '@/lib/types'
import Image from 'next/image'

interface Props {
  productData: ProductData
  mockDataSummary: MockDataSummary
  formData: FormData
}

export function SubmissionSummary({ productData, mockDataSummary, formData }: Props) {
  return (
    <div className="max-w-4xl mx-auto animate-fade-in">
      <header className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Simulation Summary
        </h1>
        <p className="text-lg text-gray-600">
          Your simulation scenario is ready. AI-powered survey coming in Phase 2.
        </p>
      </header>

      {/* Product Card */}
      <section className="card mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Product Overview</h2>
        <div className="flex gap-6">
          {productData.images[0] && (
            <div className="w-48 h-48 relative flex-shrink-0 bg-gray-50 rounded-lg overflow-hidden border">
              <Image
                src={productData.images[0]}
                alt={productData.title}
                fill
                className="object-contain"
                unoptimized
              />
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {productData.title}
            </h3>
            {productData.price && (
              <p className="text-2xl font-bold text-green-600 mb-2">
                ${productData.price.toFixed(2)}
              </p>
            )}
            {productData.brand && (
              <p className="text-gray-700 mb-1">
                <span className="font-medium">Brand:</span> {productData.brand}
              </p>
            )}
            {productData.platform && (
              <p className="text-gray-700 mb-1">
                <span className="font-medium">Platform:</span>{' '}
                {productData.platform.charAt(0).toUpperCase() + productData.platform.slice(1)}
              </p>
            )}
            {productData.rating && (
              <div className="flex items-center gap-2 mt-2">
                <span className="text-yellow-600 text-lg">★ {productData.rating.toFixed(1)}</span>
                {productData.reviewCount && (
                  <span className="text-gray-500">({productData.reviewCount} reviews)</span>
                )}
              </div>
            )}
          </div>
        </div>
        {productData.description && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <p className="text-gray-700 leading-relaxed">{productData.description}</p>
          </div>
        )}
      </section>

      {/* User Persona */}
      <section className="card mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Simulated User</h2>
        {formData.userPersona && (
          <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase block mb-1">
                  Name
                </label>
                <p className="text-gray-900 font-semibold">{formData.userPersona.name}</p>
              </div>
              <div className="col-span-2">
                <label className="text-xs font-medium text-gray-500 uppercase block mb-1">
                  Email
                </label>
                <p className="text-gray-900 font-semibold">{formData.userPersona.email}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase block mb-1">
                  Age
                </label>
                <p className="text-gray-900 font-semibold">{formData.userPersona.age} years</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase block mb-1">
                  Gender
                </label>
                <p className="text-gray-900 font-semibold">{formData.userPersona.gender}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase block mb-1">
                  Location
                </label>
                <p className="text-gray-900 font-semibold">
                  {formData.userPersona.city}, {formData.userPersona.state}
                </p>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Mock Data Statistics */}
      <section className="card mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Generated Mock Data</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm text-blue-600 font-medium mb-1">Products</p>
            <p className="text-3xl font-bold text-blue-900">{mockDataSummary.products}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <p className="text-sm text-green-600 font-medium mb-1">Users</p>
            <p className="text-3xl font-bold text-green-900">{mockDataSummary.users}</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
            <p className="text-sm text-purple-600 font-medium mb-1">Transactions</p>
            <p className="text-3xl font-bold text-purple-900">{mockDataSummary.transactions}</p>
          </div>
          <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
            <p className="text-sm text-orange-600 font-medium mb-1">Reviews</p>
            <p className="text-3xl font-bold text-orange-900">{mockDataSummary.reviews}</p>
          </div>
        </div>

        {/* Cold Start Indicators */}
        {(mockDataSummary.coldStart.product || mockDataSummary.coldStart.user) && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <h3 className="font-semibold text-yellow-900 mb-2 flex items-center gap-2">
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              Cold Start Scenario Detected
            </h3>
            <ul className="text-sm text-yellow-800 space-y-1">
              {mockDataSummary.coldStart.product && (
                <li>• Product: No existing reviews or similar product data</li>
              )}
              {mockDataSummary.coldStart.user && (
                <li>• User: No purchase history with similar products</li>
              )}
            </ul>
          </div>
        )}

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h3 className="font-semibold text-gray-900 mb-2">Scenario Description</h3>
          <p className="text-gray-700">
            {mockDataSummary.scenarioDescription || mockDataSummary.scenario}
          </p>
          <p className="text-sm text-gray-500 mt-1">Scenario ID: {mockDataSummary.scenario}</p>
        </div>
      </section>

      {/* How MOCK_DATA_AGENT Generated Data */}
      <section className="card mb-8">
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          Data Generation Process
        </h2>
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0 font-bold">
              1
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Amazon Product Scraping</h4>
              <p className="text-gray-700 text-sm">
                Scraped product details from Amazon including title, price,
                images, and {productData.reviews?.length || 0} existing reviews.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0 font-bold">
              2
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Mock User Generation</h4>
              <p className="text-gray-700 text-sm">
                Generated {mockDataSummary.users} diverse user personas with realistic
                demographics, locations, and spending patterns.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0 font-bold">
              3
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Transaction Simulation</h4>
              <p className="text-gray-700 text-sm">
                Created {mockDataSummary.transactions} realistic transactions with varied
                delivery statuses, pricing, and timeframes.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0 font-bold">
              4
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Review Generation</h4>
              <p className="text-gray-700 text-sm">
                Synthesized {mockDataSummary.reviews} reviews with sentiment distribution
                {formData.sentimentSpread &&
                  ` (${formData.sentimentSpread.good}% positive, ${formData.sentimentSpread.neutral}% neutral, ${formData.sentimentSpread.bad}% negative)`}
                .
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0 font-bold">
              5
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">Database Population</h4>
              <p className="text-gray-700 text-sm">
                All mock data has been inserted into Supabase tables (products, users,
                transactions, reviews) and is ready for the AI survey system.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Next Steps */}
      <section className="card bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200">
        <h2 className="text-2xl font-semibold text-primary-900 mb-4">Next Steps</h2>
        <div className="space-y-3 text-primary-800">
          <p className="flex items-center gap-2">
            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            Database populated with {mockDataSummary.products + mockDataSummary.users + mockDataSummary.transactions + mockDataSummary.reviews} records
          </p>
          <p className="flex items-center gap-2">
            <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
              <path
                fillRule="evenodd"
                d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                clipRule="evenodd"
              />
            </svg>
            Ready for GenAI survey generation demo
          </p>
          <p className="flex items-center gap-2">
            <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
            </svg>
            Agentic backend workflow ready to demonstrate personalized survey capabilities
          </p>
        </div>

        <div className="mt-6 p-4 bg-white rounded-lg border border-primary-300">
          <p className="text-sm text-gray-700 italic">
            The simulation is complete! Click "Next: Start Survey" to begin the AI-powered survey that uses this mock data to generate personalized questions.
          </p>
        </div>
      </section>
    </div>
  )
}
