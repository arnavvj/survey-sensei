'use client'

interface Props {
  value?: 'yes' | 'no'
  onChange: (value: 'yes' | 'no') => void
  productUrl: string
}

export function ReviewStatusField({ value, onChange }: Props) {
  const handleYesClick = () => {
    onChange('yes')
  }

  return (
    <div className="card animate-slide-in">
      <label className="block text-lg font-semibold text-gray-800 mb-3">
        2. Main Product Review History
      </label>
      <p className="text-sm text-gray-600 mb-4">
        Has this main product been reviewed by customers before?
      </p>

      <div className="flex gap-3">
        <button
          onClick={handleYesClick}
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
            <p>✅ Product reviews available! We'll use them to generate our simulation.</p>
          ) : (
            <p>No problem! We'll check if similar products have been reviewed.</p>
          )}
        </div>
      )}
    </div>
  )
}
