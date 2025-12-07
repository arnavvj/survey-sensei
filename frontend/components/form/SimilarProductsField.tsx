'use client'

interface Props {
  value?: 'yes' | 'no'
  onChange: (value: 'yes' | 'no') => void
}

export function SimilarProductsField({ value, onChange }: Props) {
  return (
    <div className="card animate-slide-in">
      <label className="block text-lg font-semibold text-gray-800 mb-3">
        4. Similar Products Review History
      </label>
      <p className="text-sm text-gray-600 mb-4">
        Have similar or comparable products been reviewed by customers?
      </p>

      <div className="flex gap-3">
        <button
          onClick={() => onChange('yes')}
          className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
            value === 'yes'
              ? 'bg-primary-600 text-white shadow-md'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Yes
        </button>
        <button
          onClick={() => onChange('no')}
          className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all ${
            value === 'no'
              ? 'bg-primary-600 text-white shadow-md'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          No
        </button>
      </div>

      {value && (
        <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
          {value === 'yes' ? (
            <p>
              Excellent! We'll generate similar products with review histories to provide
              context for our AI survey system.
            </p>
          ) : (
            <p>
              This is a <strong>cold start scenario</strong> from the product perspective.
              Our AI will work with minimal historical context.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
