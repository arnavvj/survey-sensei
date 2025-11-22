'use client'

import { useState, useEffect, useRef } from 'react'
import { FormData, FormStep, ProductData, MockDataSummary, SurveySession, SurveyResponse } from '@/lib/types'
import { ProductUrlField } from '@/components/form/ProductUrlField'
import { ReviewStatusField } from '@/components/form/ReviewStatusField'
import { SentimentSpreadField } from '@/components/form/SentimentSpreadField'
import { SimilarProductsField } from '@/components/form/SimilarProductsField'
import { UserPersonaField } from '@/components/form/UserPersonaField'
import { UserPurchaseHistoryField } from '@/components/form/UserPurchaseHistoryField'
import { UserExactProductField } from '@/components/form/UserExactProductField'
import { SubmissionSummary } from '@/components/SubmissionSummary'

export default function HomePage() {
  const [currentStep, setCurrentStep] = useState<FormStep>(1)
  const formContainerRef = useRef<HTMLDivElement>(null)
  const summaryPaneRef = useRef<HTMLDivElement>(null)
  const surveyPaneRef = useRef<HTMLDivElement>(null)
  const [formData, setFormData] = useState<FormData>({
    productUrl: '',
  })
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [mockDataSummary, setMockDataSummary] = useState<MockDataSummary | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Pane visibility states
  const [isSurveyPaneExpanded, setIsSurveyPaneExpanded] = useState(false) // Survey Sensei pane expanded (90%)
  const [isSummaryPaneMinimized, setIsSummaryPaneMinimized] = useState(false) // Summary minimized to 10%
  const [showSurveyUI, setShowSurveyUI] = useState(false) // Show Survey UI (Phase 1 Part 2)
  const [activePaneIn3PaneMode, setActivePaneIn3PaneMode] = useState<'form' | 'summary' | 'survey'>('survey') // Which pane is expanded in 3-pane mode

  // Survey states
  const [surveySession, setSurveySession] = useState<SurveySession | null>(null)
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [isLoadingSurvey, setIsLoadingSurvey] = useState(false)
  const [surveyError, setSurveyError] = useState<string | null>(null)

  const updateFormData = (updates: Partial<FormData>) => {
    setFormData((prev) => ({ ...prev, ...updates }))
  }

  // Auto-scroll to newly appeared question when currentStep changes
  useEffect(() => {
    if (!isSubmitted && formContainerRef.current && currentStep > 1) {
      setTimeout(() => {
        // Find all cards (form fields) in the container
        const cards = formContainerRef.current?.querySelectorAll('.card')
        if (cards && cards.length > 0) {
          // Scroll to the last card (newest question)
          const lastCard = cards[cards.length - 1]
          lastCard.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }, 150)
    }
  }, [currentStep, isSubmitted])

  // Toggle Survey Sensei pane
  const toggleSurveyPane = () => {
    if (showSurveyUI) {
      // In 3-pane mode
      if (activePaneIn3PaneMode === 'form') {
        // If form is expanded, go back to survey (rightmost pane)
        setActivePaneIn3PaneMode('survey')
        setTimeout(() => surveyPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      } else {
        // Expand Survey Sensei pane
        setActivePaneIn3PaneMode('form')
        setTimeout(() => formContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      }
    } else {
      // Before 3-pane mode (2-pane): toggle between form and summary
      if (isSurveyPaneExpanded) {
        setIsSurveyPaneExpanded(false)
        setIsSummaryPaneMinimized(false)
        setTimeout(() => summaryPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      } else {
        setIsSurveyPaneExpanded(true)
        setIsSummaryPaneMinimized(true)
        setTimeout(() => formContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      }
    }
  }

  // Toggle Summary pane
  const toggleSummaryPane = () => {
    if (showSurveyUI) {
      // In 3-pane mode
      if (activePaneIn3PaneMode === 'summary') {
        // If summary is expanded, go back to survey (rightmost pane)
        setActivePaneIn3PaneMode('survey')
        setTimeout(() => surveyPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      } else {
        // Expand Summary pane
        setActivePaneIn3PaneMode('summary')
        setTimeout(() => summaryPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      }
    } else {
      // Before 3-pane mode (2-pane): return to summary view and scroll to top
      setIsSurveyPaneExpanded(false)
      setIsSummaryPaneMinimized(false)
      setTimeout(() => summaryPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
    }
  }

  // Scroll SMP to top whenever it's shown in 2-pane mode
  useEffect(() => {
    if (!showSurveyUI && !isSurveyPaneExpanded && !isSummaryPaneMinimized && summaryPaneRef.current) {
      summaryPaneRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [isSurveyPaneExpanded, isSummaryPaneMinimized, showSurveyUI])

  // Toggle Survey UI pane
  const toggleSurveyUIPane = () => {
    if (showSurveyUI) {
      // In 3-pane mode: expand Survey UI pane
      setActivePaneIn3PaneMode('survey')
      setTimeout(() => surveyPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
    }
  }

  // Start survey session with backend
  const startSurveySession = async () => {
    if (!mockDataSummary) return

    setIsLoadingSurvey(true)
    setSurveyError(null)

    try {
      const response = await fetch('/api/survey/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          form_data: formData,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to start survey')
      }

      const data = await response.json()
      setSurveySession({
        session_id: data.session_id,
        question: data.question,
        question_number: data.question_number,
        total_questions: data.total_questions,
        responses: [],
      })
    } catch (error: any) {
      console.error('Error starting survey:', error)
      setSurveyError(error.message || 'Failed to start survey. Make sure the backend server is running.')
    } finally {
      setIsLoadingSurvey(false)
    }
  }

  // Submit answer and get next question
  const submitAnswer = async () => {
    if (!surveySession || selectedOptions.length === 0) return

    setIsLoadingSurvey(true)
    setSurveyError(null)

    try {
      const answer = surveySession.question?.question_type === 'multiple'
        ? selectedOptions
        : selectedOptions[0]

      const response = await fetch('/api/survey/answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: surveySession.session_id,
          answer,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit answer')
      }

      const data = await response.json()

      // Add response to history
      const newResponse: SurveyResponse = {
        question: surveySession.question!.question_text,
        answer,
        question_number: surveySession.question_number,
      }

      setSurveySession({
        ...surveySession,
        question: data.question,
        question_number: data.question_number,
        total_questions: data.total_questions,
        status: data.status,
        review_options: data.review_options,
        responses: [...surveySession.responses, newResponse],
      })

      // Clear selected options for next question
      setSelectedOptions([])
    } catch (error: any) {
      console.error('Error submitting answer:', error)
      setSurveyError(error.message || 'Failed to submit answer')
    } finally {
      setIsLoadingSurvey(false)
    }
  }

  // Toggle option selection
  const toggleOption = (option: string) => {
    if (!surveySession?.question) return

    if (surveySession.question.question_type === 'multiple') {
      // Multiple selection
      setSelectedOptions(prev =>
        prev.includes(option)
          ? prev.filter(o => o !== option)
          : [...prev, option]
      )
    } else {
      // Single selection
      setSelectedOptions([option])
    }
  }

  // Navigate to Survey UI (enter 3-pane mode)
  const handleNext = async () => {
    setShowSurveyUI(true)
    setActivePaneIn3PaneMode('survey') // Start with survey pane expanded
    // Scroll survey pane to top when transitioning
    setTimeout(() => surveyPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)

    // Start survey session
    await startSurveySession()
  }

  const handleProductFetched = (productData: ProductData) => {
    updateFormData({ productData })
    setCurrentStep(2) // Show Field 2
  }

  const handleField2Complete = (hasReviews: 'yes' | 'no') => {
    updateFormData({ hasReviews })
    if (hasReviews === 'yes') {
      setCurrentStep(3) // Go to Sentiment Spread
    } else {
      setCurrentStep(4) // Go to Similar Products
    }
  }

  const handleField3Complete = (sentimentSpread: { good: number; neutral: number; bad: number }) => {
    updateFormData({ sentimentSpread })
    setCurrentStep(5)
  }

  const handleField4Complete = (hasSimilarProductsReviewed: 'yes' | 'no') => {
    updateFormData({ hasSimilarProductsReviewed })
    setCurrentStep(5)
  }

  const handleField5Complete = (userPersona: FormData['userPersona']) => {
    updateFormData({ userPersona })
    setCurrentStep(6)
  }

  const handleField6Complete = (userHasPurchasedSimilar: 'yes' | 'no') => {
    updateFormData({ userHasPurchasedSimilar })
    // Only show Field 7 if user purchased similar products
    if (userHasPurchasedSimilar === 'yes') {
      setCurrentStep(7)
    } else {
      // Skip Field 7, mark as ready for submit
      updateFormData({ userHasPurchasedExact: 'no' })
      setCurrentStep(7) // Still set to 7 to enable submit button
    }
  }

  const handleField7Complete = (userHasPurchasedExact: 'yes' | 'no') => {
    updateFormData({ userHasPurchasedExact })
  }

  const handleSubmit = async () => {
    if (!formData.productData || !formData.userPersona) return

    setIsSubmitting(true)
    try {
      const response = await fetch('/api/mock-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      const result = await response.json()

      if (result.success) {
        setMockDataSummary(result.summary)
        setIsSubmitted(true)
      } else {
        alert(`Error: ${result.error}`)
      }
    } catch (error: any) {
      alert(`Submission failed: ${error.message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  const canSubmit = currentStep === 7 && formData.userHasPurchasedExact !== undefined

  // Calculate pane widths based on state
  const getSurveyPaneWidth = () => {
    if (!isSubmitted) return 'w-full'

    if (showSurveyUI) {
      // 3-pane mode
      return activePaneIn3PaneMode === 'form' ? 'w-[90%]' : 'w-[5%] min-w-[60px]'
    }

    // 2-pane mode (before Survey UI)
    if (isSurveyPaneExpanded) return 'w-[95%]'
    return 'w-[5%] min-w-[60px]'
  }

  const getSummaryPaneWidth = () => {
    if (showSurveyUI) {
      // 3-pane mode
      return activePaneIn3PaneMode === 'summary' ? 'w-[90%]' : 'w-[5%] min-w-[60px]'
    }

    // 2-pane mode (before Survey UI)
    if (isSummaryPaneMinimized) return 'w-[5%] min-w-[60px]'
    return 'w-[95%]'
  }

  const getSurveyUIPaneWidth = () => {
    if (!showSurveyUI) return 'w-0'
    return activePaneIn3PaneMode === 'survey' ? 'w-[90%]' : 'w-[5%] min-w-[60px]'
  }

  return (
    <main className={`min-h-screen transition-all duration-500 ${isSubmitted || showSurveyUI ? 'flex' : ''}`}>
      {/* Survey Sensei Pane (Left) */}
      <div
        ref={formContainerRef}
        onClick={
          showSurveyUI && activePaneIn3PaneMode !== 'form'
            ? toggleSurveyPane
            : !showSurveyUI && isSubmitted && !isSurveyPaneExpanded
            ? toggleSurveyPane
            : undefined
        }
        className={`transition-all duration-500 ${getSurveyPaneWidth()} ${
          showSurveyUI && activePaneIn3PaneMode !== 'form'
            ? 'bg-gray-50 cursor-pointer hover:shadow-lg flex items-center justify-center relative'
            : 'bg-gradient-to-br from-white to-gray-50'
        } overflow-y-auto ${
          !showSurveyUI && isSubmitted && !isSurveyPaneExpanded
            ? 'cursor-pointer hover:shadow-lg p-8'
            : showSurveyUI && activePaneIn3PaneMode !== 'form'
            ? ''
            : 'p-8'
        }`}
      >
        {/* Minimized vertical text in 3-pane mode */}
        {showSurveyUI && activePaneIn3PaneMode !== 'form' ? (
          <div className="fixed top-4 left-2 flex flex-col items-center gap-3 z-10">
            {/* Survey Sensei Logo - Artsy Design */}
            <div className="relative bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white rounded-xl p-2 shadow-xl">
              <div className="absolute inset-0 bg-white opacity-10 rounded-xl"></div>
              <div className="relative text-[9px] font-black tracking-wide leading-tight italic">SURVEY</div>
              <div className="relative text-[9px] font-black tracking-wide leading-tight italic">SENSEI</div>
            </div>
            <div className="fixed top-20 transform -rotate-90 origin-center whitespace-nowrap text-xs font-semibold text-gray-700 mt-8">
              Form
            </div>
          </div>
        ) : (
          <div className={`${isSubmitted && !isSurveyPaneExpanded && !showSurveyUI ? 'max-w-[100px]' : 'max-w-2xl'} mx-auto`}>
            {!isSubmitted && (
            <>
              <header className="mb-8 flex items-center gap-4">
                {/* Survey Sensei Logo */}
                <div className="relative bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white rounded-xl p-3 shadow-xl">
                  <div className="absolute inset-0 bg-white opacity-10 rounded-xl"></div>
                  <div className="relative text-sm font-black tracking-wide leading-tight italic">SURVEY</div>
                  <div className="relative text-sm font-black tracking-wide leading-tight italic">SENSEI</div>
                </div>
                <div>
                  <h1 className="text-4xl font-bold text-primary-900 mb-2">Survey Sensei</h1>
                  <p className="text-lg text-primary-700">
                    AI-Powered Survey Simulator for Amazon Products
                  </p>
                </div>
              </header>

              <div className="space-y-6">
                {/* Field 1 */}
                <ProductUrlField
                  value={formData.productUrl}
                  onChange={(url) => updateFormData({ productUrl: url })}
                  onComplete={handleProductFetched}
                  productData={formData.productData}
                />

                {/* Field 2: Review Status (reviews pre-fetched, user confirms if they exist) */}
                {currentStep >= 2 && formData.productData && (
                  <ReviewStatusField
                    value={formData.hasReviews}
                    onChange={handleField2Complete}
                    productUrl={formData.productUrl}
                  />
                )}

                {/* Field 3: Sentiment Spread (only if reviews exist) */}
                {currentStep >= 3 && formData.hasReviews === 'yes' && (
                  <SentimentSpreadField
                    value={formData.sentimentSpread}
                    onChange={handleField3Complete}
                  />
                )}

                {/* Field 4 */}
                {currentStep >= 4 && formData.hasReviews === 'no' && (
                  <SimilarProductsField
                    value={formData.hasSimilarProductsReviewed}
                    onChange={handleField4Complete}
                  />
                )}

                {/* Field 5 */}
                {currentStep >= 5 && (
                  <UserPersonaField
                    value={formData.userPersona}
                    onChange={handleField5Complete}
                  />
                )}

                {/* Field 6 */}
                {currentStep >= 6 && formData.userPersona && (
                  <UserPurchaseHistoryField
                    value={formData.userHasPurchasedSimilar}
                    onChange={handleField6Complete}
                  />
                )}

                {/* Field 7 - Only show if user purchased similar products */}
                {currentStep >= 7 && formData.userHasPurchasedSimilar === 'yes' && (
                  <UserExactProductField
                    productTitle={formData.productData?.title || 'this product'}
                    value={formData.userHasPurchasedExact}
                    onChange={handleField7Complete}
                  />
                )}

                {/* Submit Button */}
                {canSubmit && (
                  <div className="mt-8 animate-fade-in">
                    <button
                      onClick={handleSubmit}
                      disabled={isSubmitting}
                      className="btn-primary w-full py-4 text-lg font-semibold shadow-lg hover:shadow-xl disabled:opacity-50"
                    >
                      {isSubmitting ? (
                        <span className="flex items-center justify-center gap-2">
                          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Generating Mock Data...
                        </span>
                      ) : (
                        'SUBMIT'
                      )}
                    </button>
                  </div>
                )}
              </div>
            </>
          )}

          {isSubmitted && !isSurveyPaneExpanded && !showSurveyUI && (
            <div className="h-full relative">
              {/* Survey Sensei Logo - Vertically Centered at x=0 */}
              <div className="fixed top-1/2 left-0 transform -translate-y-1/2 z-20 pl-2">
                <div className="relative bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white rounded-xl p-2 shadow-xl">
                  <div className="absolute inset-0 bg-white opacity-10 rounded-xl"></div>
                  <div className="relative text-[9px] font-black tracking-wide leading-tight italic">SURVEY</div>
                  <div className="relative text-[9px] font-black tracking-wide leading-tight italic">SENSEI</div>
                </div>
              </div>

              {/* Form Title - Fixed slightly below top to avoid browser chrome */}
              <div className="fixed top-16 left-0 z-20 pl-2">
                <div className="transform -rotate-90 origin-left whitespace-nowrap text-xs font-semibold text-gray-700 ml-3">
                  Form
                </div>
              </div>
            </div>
          )}

          {/* Expanded View: Show Filled Form (Read-Only) */}
          {isSubmitted && (activePaneIn3PaneMode === 'form' || (!showSurveyUI && isSurveyPaneExpanded)) && (
            <div className="h-full p-8">
              {/* Survey Sensei Heading */}
              <h2 className="text-3xl font-bold text-gray-900 mb-6">Survey Sensei</h2>

              {/* Two Column Layout: Generated + Submitted Form */}
              <div className="grid grid-cols-2 gap-6">
                {/* Left Column: Generated Stats */}
                {mockDataSummary && (
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 mb-4">Generated Data Summary</h3>
                    <div className="space-y-4">
                      <div className="bg-white p-5 rounded-xl shadow-md border border-indigo-200">
                        <div className="text-3xl font-bold text-indigo-600 text-center">{mockDataSummary.products}</div>
                        <div className="text-sm text-gray-600 text-center font-medium mt-1">Products</div>
                      </div>
                      <div className="bg-white p-5 rounded-xl shadow-md border border-green-200">
                        <div className="text-3xl font-bold text-green-600 text-center">{mockDataSummary.users}</div>
                        <div className="text-sm text-gray-600 text-center font-medium mt-1">Users</div>
                      </div>
                      <div className="bg-white p-5 rounded-xl shadow-md border border-blue-200">
                        <div className="text-3xl font-bold text-blue-600 text-center">{mockDataSummary.transactions}</div>
                        <div className="text-sm text-gray-600 text-center font-medium mt-1">Transactions</div>
                      </div>
                      <div className="bg-white p-5 rounded-xl shadow-md border border-purple-200">
                        <div className="text-3xl font-bold text-purple-600 text-center">{mockDataSummary.reviews}</div>
                        <div className="text-sm text-gray-600 text-center font-medium mt-1">Reviews</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Right Column: Submitted Form Data */}
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-4">Form Data (Read-Only)</h3>
                  <div className="space-y-4 text-sm">
                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-2">Field 1: Product</h4>
                      <p className="text-gray-700">{formData.productData?.title || 'N/A'}</p>
                      <p className="text-xs text-gray-500 mt-1">{formData.productUrl}</p>
                    </div>

                    {formData.hasReviews === 'yes' && formData.sentimentSpread && (
                      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                        <h4 className="font-semibold text-gray-900 mb-2">Sentiment Spread</h4>
                        <div className="space-y-1">
                          <p className="text-gray-700">Good: {formData.sentimentSpread.good}%</p>
                          <p className="text-gray-700">Neutral: {formData.sentimentSpread.neutral}%</p>
                          <p className="text-gray-700">Bad: {formData.sentimentSpread.bad}%</p>
                        </div>
                      </div>
                    )}

                    {formData.hasReviews === 'no' && (
                      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                        <h4 className="font-semibold text-gray-900 mb-2">Similar Products Reviewed</h4>
                        <p className="text-gray-700">{formData.hasSimilarProductsReviewed === 'yes' ? 'Yes' : 'No'}</p>
                      </div>
                    )}

                    {formData.userPersona && (
                      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                        <h4 className="font-semibold text-gray-900 mb-2">User Persona</h4>
                        <div className="space-y-1">
                          <p className="text-gray-700"><strong>Name:</strong> {formData.userPersona.name}</p>
                          <p className="text-gray-700"><strong>Email:</strong> {formData.userPersona.email}</p>
                          <p className="text-gray-700"><strong>Age:</strong> {formData.userPersona.age}</p>
                          <p className="text-gray-700"><strong>Location:</strong> {formData.userPersona.location}</p>
                        </div>
                      </div>
                    )}

                    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                      <h4 className="font-semibold text-gray-900 mb-2">Purchase History</h4>
                      <p className="text-gray-700">Has purchased similar: {formData.userHasPurchasedSimilar === 'yes' ? 'Yes' : 'No'}</p>
                      {formData.userHasPurchasedSimilar === 'yes' && (
                        <p className="text-gray-700">Has purchased exact product: {formData.userHasPurchasedExact === 'yes' ? 'Yes' : 'No'}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          </div>
        )}
      </div>

      {/* Simulation Summary Pane (Center/Right) */}
      {isSubmitted && !showSurveyUI && mockDataSummary && formData.productData && (
        <div
          ref={summaryPaneRef}
          onClick={isSummaryPaneMinimized ? toggleSummaryPane : undefined}
          className={`transition-all duration-500 ${getSummaryPaneWidth()} ${
            isSummaryPaneMinimized ? 'bg-blue-100' : 'bg-gradient-to-br from-blue-100 to-blue-200'
          } overflow-y-auto ${
            isSummaryPaneMinimized ? 'cursor-pointer hover:shadow-lg relative' : 'p-8'
          }`}
        >
          {isSummaryPaneMinimized ? (
            // Minimized view - vertical text (positioned relative to this pane)
            <div className="absolute top-16 left-1/2 transform -translate-x-1/2 z-20">
              <div className="transform -rotate-90 whitespace-nowrap text-xs font-semibold text-blue-900">
                Summary
              </div>
            </div>
          ) : (
            // Full view with Next button
            <div>
              <SubmissionSummary
                productData={formData.productData}
                mockDataSummary={mockDataSummary}
                formData={formData}
              />

              {/* Next Button to proceed to Survey UI */}
              <div className="mt-8 flex justify-center">
                <button
                  onClick={handleNext}
                  className="btn-primary px-12 py-4 text-lg"
                >
                  Next: Start Survey
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Summary Pane in 3-pane mode */}
      {showSurveyUI && mockDataSummary && formData.productData && (
        <div
          ref={summaryPaneRef}
          onClick={activePaneIn3PaneMode !== 'summary' ? toggleSummaryPane : undefined}
          className={`transition-all duration-500 ${getSummaryPaneWidth()} ${
            activePaneIn3PaneMode !== 'summary'
              ? 'bg-blue-100'
              : 'bg-gradient-to-br from-blue-100 to-blue-200'
          } overflow-y-auto ${
            activePaneIn3PaneMode !== 'summary'
              ? 'cursor-pointer hover:shadow-lg flex items-center justify-center relative'
              : 'p-8'
          }`}
        >
          {activePaneIn3PaneMode !== 'summary' ? (
            <div className="absolute top-16 left-1/2 transform -translate-x-1/2 z-20">
              <div className="transform -rotate-90 whitespace-nowrap text-xs font-semibold text-blue-900">
                Summary
              </div>
            </div>
          ) : (
            <SubmissionSummary
              productData={formData.productData}
              mockDataSummary={mockDataSummary}
              formData={formData}
            />
          )}
        </div>
      )}

      {/* Survey UI Pane (Right) in 3-pane mode */}
      {showSurveyUI && (
        <div
          ref={surveyPaneRef}
          onClick={activePaneIn3PaneMode !== 'survey' ? toggleSurveyUIPane : undefined}
          className={`transition-all duration-500 ${getSurveyUIPaneWidth()} ${
            activePaneIn3PaneMode !== 'survey'
              ? 'bg-emerald-50'
              : 'bg-gradient-to-br from-emerald-50 to-emerald-100'
          } overflow-y-auto ${
            activePaneIn3PaneMode !== 'survey'
              ? 'cursor-pointer hover:shadow-lg flex items-center justify-center relative'
              : ''
          }`}
        >
          {activePaneIn3PaneMode !== 'survey' ? (
            <div className="fixed top-4 flex flex-col items-center w-full z-10">
              <div className="transform -rotate-90 origin-center whitespace-nowrap text-xs font-semibold text-emerald-900 mt-12">
                Survey
              </div>
            </div>
          ) : (
            <div className="flex flex-col h-full">
            {/* Survey Questions Area (Top 65%) */}
            <div className="h-[65%] bg-white p-8 overflow-y-auto border-b-2 border-gray-200">
              <div className="max-w-3xl mx-auto">
                <h2 className="text-3xl font-bold text-gray-900 mb-6">
                  Personalized Survey
                </h2>

              {/* Loading State */}
              {isLoadingSurvey && !surveySession && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <svg className="animate-spin h-12 w-12 text-primary-600 mx-auto mb-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <p className="text-gray-600">Starting survey session...</p>
                  </div>
                </div>
              )}

              {/* Error State */}
              {surveyError && (
                <div className="p-6 bg-red-50 border-l-4 border-red-500 rounded-lg mb-6">
                  <p className="text-sm text-red-700 mb-2">
                    <strong>Error:</strong> {surveyError}
                  </p>
                  <button
                    onClick={startSurveySession}
                    className="text-sm text-red-600 underline hover:text-red-800"
                  >
                    Try again
                  </button>
                </div>
              )}

              {/* Survey Question */}
              {surveySession && surveySession.status !== 'completed' && surveySession.question && (
                <div className="space-y-6">
                  <div className="p-6 bg-[#BDF5BD] border-2 border-gray-200 rounded-lg shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-xl font-semibold text-gray-900">
                        Question {surveySession.question_number} of {surveySession.total_questions}
                      </h3>
                      {surveySession.question.question_type === 'multiple' && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Multiple Choice</span>
                      )}
                    </div>
                    <p className="text-gray-900 mb-4 text-lg">
                      {surveySession.question.question_text}
                    </p>
                    <div className="space-y-2">
                      {surveySession.question.options.map((option, idx) => (
                        <button
                          key={idx}
                          onClick={() => toggleOption(option)}
                          className={`w-full text-left p-3 border-2 rounded-lg transition-all text-gray-900 font-medium ${
                            selectedOptions.includes(option)
                              ? 'border-primary-600 bg-primary-100'
                              : 'border-gray-300 hover:border-primary-500 hover:bg-green-200'
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {surveySession.question?.question_type === 'multiple' && (
                              <div className={`w-5 h-5 border-2 rounded ${selectedOptions.includes(option) ? 'bg-primary-600 border-primary-600' : 'border-gray-300'}`}>
                                {selectedOptions.includes(option) && (
                                  <svg className="w-full h-full text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                  </svg>
                                )}
                              </div>
                            )}
                            <span>{option}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={submitAnswer}
                      disabled={selectedOptions.length === 0 || isLoadingSurvey}
                      className="mt-4 w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoadingSurvey ? 'Submitting...' : 'Submit Answer'}
                    </button>
                    {surveySession.question.reasoning && (
                      <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-gray-700">
                        <strong>Why we're asking:</strong> {surveySession.question.reasoning}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Survey Completed */}
              {surveySession && surveySession.status === 'completed' && (
                <div className="p-6 bg-green-50 border-l-4 border-green-500 rounded-lg">
                  <p className="text-lg text-green-700 font-semibold mb-2">
                    Survey Completed!
                  </p>
                  <p className="text-sm text-green-600">
                    Thank you for completing the survey. Review options are available below.
                  </p>
                </div>
              )}
            </div>
            </div>

            {/* Answer Stack Area (Bottom 35%) */}
            <div className="h-[35%] bg-emerald-600 p-6 overflow-y-auto">
            <div className="max-w-3xl mx-auto">
              <h3 className="text-lg font-semibold text-white mb-4">
                Your Responses ({surveySession?.responses.length || 0})
              </h3>

              {/* Response Stack */}
              <div className="space-y-3">
                {surveySession && surveySession.responses.length > 0 ? (
                  surveySession.responses.map((response, idx) => (
                    <div key={idx} className="p-4 bg-white rounded-lg shadow-sm border-l-4 border-emerald-700">
                      <p className="text-sm text-gray-600 mb-1">
                        Q{response.question_number}: {response.question}
                      </p>
                      <p className="text-gray-900 font-medium">
                        {Array.isArray(response.answer) ? response.answer.join(', ') : response.answer}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="p-4 bg-emerald-500 border-2 border-dashed border-emerald-300 rounded-lg">
                    <p className="text-sm text-emerald-50 italic">
                      Your answered questions will stack here as you progress through the survey...
                    </p>
                  </div>
                )}
              </div>

              {/* Generate Review Button (appears after completing questions) */}
              {surveySession && surveySession.status === 'completed' && (
                <div className="mt-6">
                  <button className="w-full btn-primary py-4 text-lg">
                    Generate Product Review
                  </button>
                </div>
              )}
            </div>
            </div>
            </div>
          )}
        </div>
      )}
    </main>
  )
}
