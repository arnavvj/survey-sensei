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
    <div className="w-full bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200 py-4 px-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between">
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

              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-4 mt-[-24px]">
                  <div
                    className={`h-full transition-all ${
                      step.status === 'finish' ? 'bg-green-500' : 'bg-gray-300'
                    }`}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
