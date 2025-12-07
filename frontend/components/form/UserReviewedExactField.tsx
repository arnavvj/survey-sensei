'use client'

interface Props {
  productTitle: string
  value?: 'yes' | 'no'
  onChange: (value: 'yes' | 'no') => void
}

export function UserReviewedExactField({ productTitle, value, onChange }: Props) {
  return (
    <div className="card animate-slide-in">
      <label className="block text-lg font-semibold text-gray-800 mb-3">
        9. User Review History (Exact Product)
      </label>
      <p className="text-sm text-gray-600 mb-4">
        Has this user already reviewed this specific product?
      </p>
      <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
        <p className="text-sm font-medium text-purple-900">
          Product: <span className="font-semibold">{productTitle}</span>
        </p>
      </div>

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
              🎯 <strong>Highest confidence scenario!</strong> The user has already reviewed this exact product. We'll generate highly specific follow-up survey questions.
            </p>
          ) : (
            <p>
              User purchased this product but hasn't reviewed it yet. Perfect for capturing first impressions and detailed feedback.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
