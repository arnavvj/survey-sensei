interface Step {
  title: string
  status: 'wait' | 'process' | 'finish'
  onClick?: () => void
}

interface StepsProps {
  steps: Step[]
}

export function Steps({ steps }: StepsProps) {
  return (
    <div className="w-full bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200 py-4 px-8 relative">
      {/* Survey Sensei Logo - Top Left (Absolute) */}
      <div className="absolute left-8 top-1/2 transform -translate-y-1/2">
        <div className="relative bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white rounded-xl p-3 shadow-xl">
          <div className="absolute inset-0 bg-white opacity-10 rounded-xl"></div>
          <div className="relative text-sm font-black tracking-wide leading-tight italic">SURVEY</div>
          <div className="relative text-sm font-black tracking-wide leading-tight italic">SENSEI</div>
        </div>
      </div>

      {/* Steps - Centered */}
      <div className="flex items-center justify-center">
        <div className="flex items-center justify-between max-w-3xl">
            {steps.map((step, index) => (
              <div key={index} className="flex items-center flex-1">
              {/* Step Circle and Label */}
              <div
                className={`flex flex-col items-center ${
                  step.onClick ? 'cursor-pointer' : ''
                } group`}
                onClick={step.onClick}
              >
                {/* Circle */}
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm transition-all ${
                    step.status === 'finish'
                      ? 'bg-green-500 text-white group-hover:bg-green-600'
                      : step.status === 'process'
                      ? 'bg-blue-500 text-white ring-4 ring-blue-200 group-hover:bg-blue-600'
                      : 'bg-gray-300 text-gray-600 group-hover:bg-gray-400'
                  }`}
                >
                  {step.status === 'finish' ? (
                    <svg
                      className="w-5 h-5"
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
                  ) : (
                    index + 1
                  )}
                </div>
                {/* Label */}
                <div
                  className={`mt-2 text-xs font-medium ${
                    step.status === 'process'
                      ? 'text-blue-600'
                      : step.status === 'finish'
                      ? 'text-green-600'
                      : 'text-gray-500'
                  }`}
                >
                  {step.title}
                </div>
              </div>

              {/* Arrow Connector */}
              {index < steps.length - 1 && (
                <div className="flex items-center mx-4 mt-[-24px]">
                  <svg
                    className={`w-6 h-6 transition-all ${
                      step.status === 'finish' ? 'text-green-500' : 'text-gray-300'
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 7l5 5m0 0l-5 5m5-5H6"
                    />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
