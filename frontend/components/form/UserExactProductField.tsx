'use client'

interface Props {
  productTitle: string
  value?: 'yes' | 'no'
  onChange: (value: 'yes' | 'no') => void
}

export function UserExactProductField({ productTitle, value, onChange }: Props) {
  return (
    <div className="card animate-slide-in">
      <label className="block text-lg font-semibold text-gray-800 mb-3">
        8. User Purchase History (Exact Product)
      </label>
      <p className="text-sm text-gray-600 mb-4">
        Has this user bought or returned this exact product before?
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
              The user has prior experience with this exact product. This will enable
              deeper, more specific survey questions.
            </p>
          ) : (
            <p>
              This is the user's first time purchasing this specific product. The survey
              will focus on expectations and initial impressions.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
