'use client'

import { useState, useEffect, useRef } from 'react'
import { FormData, FormStep, ProductData, MockDataSummary, SurveySession, SurveyResponse, ReviewOption } from '@/lib/types'
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
  const reviewPaneRef = useRef<HTMLDivElement>(null)
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
  const [showReviewPane, setShowReviewPane] = useState(false) // Show Review Pane (4-pane mode)
  const [activePaneIn3PaneMode, setActivePaneIn3PaneMode] = useState<'form' | 'summary' | 'survey'>('survey') // Which pane is expanded in 3-pane mode
  const [activePaneIn4PaneMode, setActivePaneIn4PaneMode] = useState<'form' | 'summary' | 'survey' | 'review'>('review') // Which pane is expanded in 4-pane mode

  // Survey states
  const [surveySession, setSurveySession] = useState<SurveySession | null>(null)
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [otherText, setOtherText] = useState<string>('')  // For "Other" option text input
  const [isLoadingSurvey, setIsLoadingSurvey] = useState(false)
  const [surveyError, setSurveyError] = useState<string | null>(null)
  const [skipWarning, setSkipWarning] = useState<string | null>(null)

  // Review states (Agent 4)
  const [reviewOptions, setReviewOptions] = useState<ReviewOption[]>([])
  const [sentimentBand, setSentimentBand] = useState<string>('')
  const [isGeneratingReviews, setIsGeneratingReviews] = useState(false)
  const [selectedReviewIndex, setSelectedReviewIndex] = useState<number | null>(null)
  const [isReviewSubmitted, setIsReviewSubmitted] = useState(false)

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
    if (showReviewPane) {
      // In 4-pane mode
      if (activePaneIn4PaneMode === 'form') {
        // If form is expanded, go back to review (rightmost pane)
        setActivePaneIn4PaneMode('review')
        setTimeout(() => reviewPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      } else {
        // Expand Survey Sensei pane
        setActivePaneIn4PaneMode('form')
        setTimeout(() => formContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      }
    } else if (showSurveyUI) {
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
    if (showReviewPane) {
      // In 4-pane mode
      if (activePaneIn4PaneMode === 'summary') {
        // If summary is expanded, go back to review (rightmost pane)
        setActivePaneIn4PaneMode('review')
        setTimeout(() => reviewPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      } else {
        // Expand Summary pane
        setActivePaneIn4PaneMode('summary')
        setTimeout(() => summaryPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      }
    } else if (showSurveyUI) {
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

  // Scroll Summary pane to top when form is first submitted (FP -> SMP transition)
  useEffect(() => {
    if (isSubmitted && !showSurveyUI && summaryPaneRef.current) {
      setTimeout(() => {
        summaryPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
      }, 100)
    }
  }, [isSubmitted, showSurveyUI])

  // Toggle Survey UI pane
  const toggleSurveyUIPane = () => {
    if (showReviewPane) {
      // In 4-pane mode
      if (activePaneIn4PaneMode === 'survey') {
        // If survey is expanded, go back to review (rightmost pane)
        setActivePaneIn4PaneMode('review')
        setTimeout(() => reviewPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      } else {
        // Expand Survey UI pane
        setActivePaneIn4PaneMode('survey')
        setTimeout(() => surveyPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
      }
    } else if (showSurveyUI) {
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
          user_id: mockDataSummary.mainUserId || 'unknown',
          item_id: mockDataSummary.mainProductId || 'unknown',
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

  // Generate review options using Agent 4
  const generateReviews = async (sessionId: string) => {
    setIsGeneratingReviews(true)
    setSurveyError(null)

    try {
      console.log('Generating reviews for session:', sessionId)
      const response = await fetch('/api/reviews/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
        }),
      })

      console.log('Generate reviews response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('Generate reviews error response:', errorData)
        throw new Error(errorData.error || `Failed to generate reviews (${response.status})`)
      }

      const data = await response.json()
      console.log('Generated reviews data:', data)

      setReviewOptions(data.review_options)
      setSentimentBand(data.sentiment_band)

      // Transition to 4-pane mode with Review Pane
      setShowReviewPane(true)
      setActivePaneIn4PaneMode('review')
      setTimeout(() => reviewPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
    } catch (error: any) {
      console.error('Error generating reviews:', error)
      setSurveyError(error.message || 'Failed to generate reviews')
    } finally {
      setIsGeneratingReviews(false)
    }
  }

  // Regenerate review options (Refresh button)
  const regenerateReviews = async () => {
    if (!surveySession?.session_id) return

    setIsGeneratingReviews(true)
    setSurveyError(null)

    try {
      console.log('Regenerating reviews for session:', surveySession.session_id)
      const response = await fetch('/api/reviews/regenerate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: surveySession.session_id,
        }),
      })

      console.log('Regenerate reviews response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        console.error('Regenerate reviews error response:', errorData)
        throw new Error(errorData.error || `Failed to regenerate reviews (${response.status})`)
      }

      const data = await response.json()
      console.log('Regenerated reviews data:', data)

      setReviewOptions(data.review_options)
      setSentimentBand(data.sentiment_band)
      setSelectedReviewIndex(null) // Clear selection
    } catch (error: any) {
      console.error('Error regenerating reviews:', error)
      setSurveyError(error.message || 'Failed to regenerate reviews')
    } finally {
      setIsGeneratingReviews(false)
    }
  }

  // Submit answer and get next question
  const submitAnswer = async () => {
    if (!surveySession || selectedOptions.length === 0) return

    setIsLoadingSurvey(true)
    setSurveyError(null)
    setSkipWarning(null)

    try {
      // Handle "Other" option with text input
      let finalAnswer = surveySession.question?.allow_multiple
        ? selectedOptions.map(opt => {
            if (opt.toLowerCase() === 'other' && otherText.trim()) {
              return `Other: ${otherText.trim()}`
            }
            return opt
          })
        : selectedOptions[0].toLowerCase() === 'other' && otherText.trim()
          ? `Other: ${otherText.trim()}`
          : selectedOptions[0]

      const response = await fetch('/api/survey/answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: surveySession.session_id,
          answer: finalAnswer,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const errorMessage = errorData.detail || errorData.error || 'Failed to submit answer'
        throw new Error(errorMessage)
      }

      const data = await response.json()

      // Add response to history
      const newResponse: SurveyResponse = {
        question: surveySession.question!.question_text,
        answer: finalAnswer,
        question_number: surveySession.question_number,
      }

      // Check if survey is completed
      if (data.status === 'survey_completed') {
        // Update session status
        setSurveySession({
          ...surveySession,
          status: 'survey_completed',
          responses: [...surveySession.responses, newResponse],
        })

        // Automatically generate reviews using Agent 4
        await generateReviews(surveySession.session_id)
      } else {
        // Continue with next question
        setSurveySession({
          ...surveySession,
          question: data.question,
          question_number: data.question_number,
          total_questions: data.total_questions,
          status: data.status,
          responses: [...surveySession.responses, newResponse],
        })
      }

      // Clear selected options and other text for next question
      setSelectedOptions([])
      setOtherText('')
    } catch (error: any) {
      console.error('Error submitting answer:', error)
      setSurveyError(error.message || 'Failed to submit answer')
    } finally {
      setIsLoadingSurvey(false)
    }
  }

  // Skip current question
  const skipQuestion = async () => {
    if (!surveySession?.session_id) return

    setIsLoadingSurvey(true)
    setSurveyError(null)
    setSkipWarning(null)

    try {
      const response = await fetch('/api/survey/skip', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: surveySession.session_id,
        }),
      })

      const data = await response.json()

      if (!response.ok) {
        // Show skip limit warning
        setSkipWarning(data.error || 'Unable to skip this question')
        return
      }

      // Clear selections for next question
      setSelectedOptions([])
      setOtherText('')

      // Check if survey is completed
      if (data.status === 'survey_completed') {
        setSurveySession({
          ...surveySession,
          status: 'survey_completed',
        })
        await generateReviews(surveySession.session_id)
      } else {
        // Continue with next question
        setSurveySession({
          ...surveySession,
          question: data.question,
          question_number: data.question_number,
          total_questions: data.total_questions,
          status: data.status,
        })
      }
    } catch (error: any) {
      console.error('Error skipping question:', error)
      setSurveyError(error.message || 'Failed to skip question')
    } finally {
      setIsLoadingSurvey(false)
    }
  }

  // Toggle option selection
  const toggleOption = (option: string) => {
    if (!surveySession?.question) return

    // Handle "All of the above" logic for multi-select questions
    if (surveySession.question.allow_multiple && option.toLowerCase().includes('all of the above')) {
      if (selectedOptions.includes(option)) {
        // Unselecting "All of the above" - revert to multi-select mode
        setSelectedOptions([])
      } else {
        // Selecting "All of the above" - make it single selection
        setSelectedOptions([option])
      }
      return
    }

    // If "All of the above" was previously selected, unselect it
    const allOfAboveOption = surveySession.question.options.find(opt =>
      opt.toLowerCase().includes('all of the above')
    )
    if (allOfAboveOption && selectedOptions.includes(allOfAboveOption)) {
      setSelectedOptions([option])
      return
    }

    if (surveySession.question.allow_multiple) {
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

  // Submit selected review
  const submitReview = async () => {
    if (!surveySession?.session_id || selectedReviewIndex === null) return

    setIsLoadingSurvey(true)
    setSurveyError(null)

    try {
      const response = await fetch('/api/survey/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: surveySession.session_id,
          selected_review_index: selectedReviewIndex,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to submit review')
      }

      const data = await response.json()

      // Update session to show review has been submitted
      setSurveySession({
        ...surveySession,
        status: 'completed',
      })
      setIsReviewSubmitted(true)

      console.log('Review submitted successfully:', data)
    } catch (error: any) {
      console.error('Error submitting review:', error)
      setSurveyError(error.message || 'Failed to submit review')
    } finally {
      setIsLoadingSurvey(false)
    }
  }

  // Edit a previous answer (branching)
  const editPreviousAnswer = async (questionNumber: number, newAnswer: string) => {
    if (!surveySession?.session_id) return

    setIsLoadingSurvey(true)
    setSurveyError(null)

    try {
      const response = await fetch('/api/survey/edit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: surveySession.session_id,
          question_number: questionNumber,
          answer: newAnswer,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to edit answer')
      }

      const data = await response.json()

      // Remove responses after the edited question
      const updatedResponses = surveySession.responses.slice(0, questionNumber - 1)

      // Add the new answer
      const newResponse: SurveyResponse = {
        question: surveySession.responses[questionNumber - 1].question,
        answer: newAnswer,
        question_number: questionNumber,
      }
      updatedResponses.push(newResponse)

      // Update session with new question
      setSurveySession({
        ...surveySession,
        question: data.question,
        question_number: data.question_number,
        total_questions: data.total_questions,
        status: data.status,
        responses: updatedResponses,
      })

      // Clear selected options for next question
      setSelectedOptions([])
    } catch (error: any) {
      console.error('Error editing answer:', error)
      setSurveyError(error.message || 'Failed to edit answer')
    } finally {
      setIsLoadingSurvey(false)
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
        // Scroll Summary pane to top after form submission
        setTimeout(() => {
          summaryPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' })
        }, 200)
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

    if (showReviewPane) {
      // 4-pane mode
      return activePaneIn4PaneMode === 'form' ? 'w-[88%]' : 'w-[4%] min-w-[60px]'
    }

    if (showSurveyUI) {
      // 3-pane mode
      return activePaneIn3PaneMode === 'form' ? 'w-[90%]' : 'w-[5%] min-w-[60px]'
    }

    // 2-pane mode (before Survey UI)
    if (isSurveyPaneExpanded) return 'w-[95%]'
    return 'w-[5%] min-w-[60px]'
  }

  const getSummaryPaneWidth = () => {
    if (showReviewPane) {
      // 4-pane mode
      return activePaneIn4PaneMode === 'summary' ? 'w-[88%]' : 'w-[4%] min-w-[60px]'
    }

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

    if (showReviewPane) {
      // 4-pane mode
      return activePaneIn4PaneMode === 'survey' ? 'w-[88%]' : 'w-[4%] min-w-[60px]'
    }

    // 3-pane mode
    return activePaneIn3PaneMode === 'survey' ? 'w-[90%]' : 'w-[5%] min-w-[60px]'
  }

  const getReviewPaneWidth = () => {
    if (!showReviewPane) return 'w-0'
    return activePaneIn4PaneMode === 'review' ? 'w-[88%]' : 'w-[4%] min-w-[60px]'
  }

  return (
    <main className={`min-h-screen transition-all duration-500 ${isSubmitted || showSurveyUI ? 'flex' : ''}`}>
      {/* Survey Sensei Pane (Left) */}
      <div
        ref={formContainerRef}
        onClick={
          showReviewPane && activePaneIn4PaneMode !== 'form'
            ? toggleSurveyPane
            : showSurveyUI && activePaneIn3PaneMode !== 'form'
            ? toggleSurveyPane
            : !showSurveyUI && isSubmitted && !isSurveyPaneExpanded
            ? toggleSurveyPane
            : undefined
        }
        className={`transition-all duration-500 ${getSurveyPaneWidth()} ${
          (showReviewPane && activePaneIn4PaneMode !== 'form') || (showSurveyUI && activePaneIn3PaneMode !== 'form')
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
        {/* Minimized vertical text in 3-pane or 4-pane mode */}
        {((showSurveyUI && activePaneIn3PaneMode !== 'form') || (showReviewPane && activePaneIn4PaneMode !== 'form')) ? (
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
          </div>
        )}

        {/* Minimized Form View (2-pane mode only) - Moved outside */}
        {isSubmitted && !isSurveyPaneExpanded && !showSurveyUI && !showReviewPane && (
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

        {/* Expanded View: Show Filled Form (Read-Only) - Always visible after form submission */}
          {(() => {
            const shouldShowFrozenForm = isSubmitted && (
              (showReviewPane && activePaneIn4PaneMode === 'form') ||
              (!showReviewPane && showSurveyUI && activePaneIn3PaneMode === 'form') ||
              (!showSurveyUI && isSurveyPaneExpanded)
            );

            // Debug logging
            if (isSubmitted) {
              console.log('FPE Debug:', {
                isSubmitted,
                showReviewPane,
                activePaneIn4PaneMode,
                showSurveyUI,
                activePaneIn3PaneMode,
                isSurveyPaneExpanded,
                shouldShowFrozenForm,
                isReviewSubmitted,
              });
            }

            return shouldShowFrozenForm;
          })() && (
            <div className="h-full p-8 overflow-y-auto">
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

      {/* Summary Pane in 3-pane or 4-pane mode */}
      {showSurveyUI && mockDataSummary && formData.productData && (
        <div
          ref={summaryPaneRef}
          onClick={
            showReviewPane && activePaneIn4PaneMode !== 'summary'
              ? toggleSummaryPane
              : activePaneIn3PaneMode !== 'summary'
              ? toggleSummaryPane
              : undefined
          }
          className={`transition-all duration-500 ${getSummaryPaneWidth()} ${
            (showReviewPane && activePaneIn4PaneMode !== 'summary') || (!showReviewPane && activePaneIn3PaneMode !== 'summary')
              ? 'bg-blue-100'
              : 'bg-gradient-to-br from-blue-100 to-blue-200'
          } overflow-y-auto ${
            (showReviewPane && activePaneIn4PaneMode !== 'summary') || (!showReviewPane && activePaneIn3PaneMode !== 'summary')
              ? 'cursor-pointer hover:shadow-lg flex items-center justify-center relative'
              : 'p-8'
          }`}
        >
          {((showReviewPane && activePaneIn4PaneMode !== 'summary') || (!showReviewPane && activePaneIn3PaneMode !== 'summary')) ? (
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

      {/* Survey UI Pane in 3-pane or 4-pane mode */}
      {showSurveyUI && (
        <div
          ref={surveyPaneRef}
          onClick={
            showReviewPane && activePaneIn4PaneMode !== 'survey'
              ? toggleSurveyUIPane
              : !showReviewPane && activePaneIn3PaneMode !== 'survey'
              ? toggleSurveyUIPane
              : undefined
          }
          className={`transition-all duration-500 ${getSurveyUIPaneWidth()} ${
            (showReviewPane && activePaneIn4PaneMode !== 'survey') || (!showReviewPane && activePaneIn3PaneMode !== 'survey')
              ? 'bg-emerald-50'
              : 'bg-gradient-to-br from-emerald-50 to-emerald-100'
          } overflow-y-auto ${
            (showReviewPane && activePaneIn4PaneMode !== 'survey') || (!showReviewPane && activePaneIn3PaneMode !== 'survey')
              ? 'cursor-pointer hover:shadow-lg flex items-center justify-center relative'
              : ''
          }`}
        >
          {((showReviewPane && activePaneIn4PaneMode !== 'survey') || (!showReviewPane && activePaneIn3PaneMode !== 'survey')) ? (
            <div className="absolute top-16 left-1/2 transform -translate-x-1/2 z-20">
              <div className="transform -rotate-90 whitespace-nowrap text-xs font-semibold text-emerald-900">
                Survey
              </div>
            </div>
          ) : (
            <div className="flex flex-col h-full">
            {/* Survey Questions Area (Top 65%) */}
            <div className="h-[65%] bg-gradient-to-br from-white via-emerald-50 to-white p-8 overflow-y-auto border-b-4 border-emerald-400 shadow-inner">
              <div className="max-w-3xl mx-auto">
                <div className="flex items-center gap-3 mb-6">
                  <div className="bg-gradient-to-r from-emerald-500 to-teal-600 text-white p-3 rounded-xl shadow-lg">
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                  </div>
                  <h2 className="text-3xl font-bold bg-gradient-to-r from-emerald-700 to-teal-700 bg-clip-text text-transparent">
                    Personalized Survey
                  </h2>
                </div>

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
                  <div className="p-6 bg-gradient-to-br from-emerald-100 via-teal-50 to-emerald-100 border-2 border-emerald-300 rounded-xl shadow-lg hover:shadow-xl transition-shadow">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-xl font-bold text-emerald-900 flex items-center gap-2">
                        <span className="bg-emerald-600 text-white px-3 py-1 rounded-lg text-sm">
                          {surveySession.question_number}/{surveySession.total_questions}
                        </span>
                        <span>Question {surveySession.question_number}</span>
                      </h3>
                      <div className="flex items-center gap-2">
                        {surveySession.question.allow_multiple && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Multiple Selection</span>
                        )}
                        <button
                          onClick={startSurveySession}
                          disabled={isLoadingSurvey}
                          className="text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-800 px-3 py-1.5 rounded flex items-center gap-1 transition-colors disabled:opacity-50"
                          title="Restart survey with current form data"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                          Restart Survey
                        </button>
                      </div>
                    </div>
                    <p className="text-gray-900 mb-5 text-lg font-medium leading-relaxed">
                      {surveySession.question.question_text}
                    </p>
                    <div className="space-y-3">
                      {surveySession.question.options.map((option, idx) => (
                        <div key={idx}>
                          <button
                            onClick={() => !isLoadingSurvey && toggleOption(option)}
                            disabled={isLoadingSurvey}
                            className={`w-full text-left p-4 border-2 rounded-xl transition-all duration-200 text-gray-900 font-medium shadow-sm hover:shadow-md ${
                              selectedOptions.includes(option)
                                ? 'border-emerald-600 bg-gradient-to-r from-emerald-100 to-teal-100 scale-[1.02] shadow-md'
                                : 'border-gray-300 hover:border-emerald-500 hover:bg-gradient-to-r hover:from-emerald-50 hover:to-teal-50'
                            } ${isLoadingSurvey ? 'opacity-50 cursor-not-allowed' : ''}`}
                          >
                            <div className="flex items-center gap-3">
                              {surveySession.question?.allow_multiple && (
                                <div className={`w-6 h-6 border-2 rounded-md shadow-sm transition-all ${selectedOptions.includes(option) ? 'bg-emerald-600 border-emerald-600 scale-110' : 'border-gray-400 bg-white'}`}>
                                  {selectedOptions.includes(option) && (
                                    <svg className="w-full h-full text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                                    </svg>
                                  )}
                                </div>
                              )}
                              {!surveySession.question?.allow_multiple && (
                                <div className={`w-6 h-6 border-2 rounded-full shadow-sm transition-all ${selectedOptions.includes(option) ? 'bg-emerald-600 border-emerald-600 scale-110' : 'border-gray-400 bg-white'}`}>
                                  {selectedOptions.includes(option) && (
                                    <div className="w-full h-full flex items-center justify-center">
                                      <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
                                    </div>
                                  )}
                                </div>
                              )}
                              <span>{option}</span>
                            </div>
                          </button>
                          {/* "Other" text input */}
                          {option.toLowerCase() === 'other' && selectedOptions.includes(option) && (
                            <input
                              type="text"
                              value={otherText}
                              onChange={(e) => setOtherText(e.target.value)}
                              placeholder="Please specify..."
                              className="mt-2 w-full p-3 border-2 border-emerald-300 rounded-lg focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200 outline-none transition-all"
                              disabled={isLoadingSurvey}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                    {/* Skip Warning Message */}
                    {skipWarning && (
                      <div className="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg">
                        <div className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                          <div>
                            <p className="text-sm text-yellow-800 font-medium">{skipWarning}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    <div className="mt-5 flex gap-3">
                      <button
                        onClick={submitAnswer}
                        disabled={selectedOptions.length === 0 || isLoadingSurvey || (selectedOptions.includes('Other') && !otherText.trim())}
                        className="flex-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white py-4 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-lg"
                      >
                        {isLoadingSurvey ? (
                          <span className="flex items-center justify-center gap-2">
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Submitting...
                          </span>
                        ) : (
                          'Submit Answer'
                        )}
                      </button>
                      <button
                        onClick={skipQuestion}
                        disabled={isLoadingSurvey}
                        className="px-6 bg-gray-200 hover:bg-gray-300 text-gray-700 py-4 rounded-xl font-semibold text-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        title="Skip this question if it's not relevant to your feedback"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Skip
                      </button>
                    </div>
                    {surveySession.question.reasoning && (
                      <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-cyan-50 border-l-4 border-blue-500 rounded-lg text-sm text-gray-700 shadow-sm">
                        <div className="flex items-start gap-2">
                          <svg className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          <div>
                            <strong className="text-blue-900">Why we're asking:</strong> {surveySession.question.reasoning}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Survey Completed */}
              {surveySession && surveySession.status === 'completed' && (
                <div className="p-6 bg-green-50 border-l-4 border-green-500 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="text-lg text-green-700 font-semibold mb-2">
                        Survey Completed!
                      </p>
                      <p className="text-sm text-green-600">
                        Thank you for completing the survey. Review options are available below.
                      </p>
                    </div>
                    <button
                      onClick={startSurveySession}
                      disabled={isLoadingSurvey}
                      className="text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-800 px-3 py-1.5 rounded flex items-center gap-1 transition-colors disabled:opacity-50 whitespace-nowrap"
                      title="Restart survey with current form data"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Restart Survey
                    </button>
                  </div>
                </div>
              )}
            </div>
            </div>

            {/* Answer Stack Area (Bottom 35%) */}
            <div className="h-[35%] bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-700 p-6 overflow-y-auto shadow-inner">
            <div className="max-w-3xl mx-auto">
              <div className="flex items-center gap-3 mb-5">
                <div className="bg-white/20 backdrop-blur-sm p-2 rounded-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-bold text-white">
                  Your Responses ({surveySession?.responses.length || 0})
                </h3>
              </div>

              {/* Response Stack */}
              <div className="space-y-3">
                {surveySession && surveySession.responses.length > 0 ? (
                  surveySession.responses.map((response, idx) => {
                    // Disable editing after reviews are generated
                    const isEditingDisabled = surveySession.status === 'reviews_generated' || surveySession.status === 'completed'

                    return (
                    <div
                      key={idx}
                      className={`p-4 bg-white/95 backdrop-blur-sm rounded-xl shadow-md border-l-4 border-teal-400 transition-all duration-200 group ${
                        isEditingDisabled
                          ? 'opacity-75 cursor-not-allowed'
                          : 'hover:border-yellow-400 hover:bg-white cursor-pointer hover:shadow-lg hover:scale-[1.01]'
                      }`}
                      onClick={() => {
                        if (isEditingDisabled) {
                          alert('Survey responses cannot be edited after reviews have been generated. Please restart the survey for a new iteration.')
                          return
                        }
                        if (confirm(`Edit your answer to question ${response.question_number}?\n\nThis will discard all answers after this question and let you continue from here.`)) {
                          const newAnswer = prompt(
                            `${response.question}\n\nCurrent answer: ${Array.isArray(response.answer) ? response.answer.join(', ') : response.answer}\n\nEnter new answer:`,
                            Array.isArray(response.answer) ? response.answer.join(', ') : response.answer
                          )
                          if (newAnswer) {
                            editPreviousAnswer(response.question_number, newAnswer)
                          }
                        }
                      }}
                      title={isEditingDisabled ? 'Editing disabled after review generation' : 'Click to edit this answer'}
                    >
                      <div className="flex items-start gap-2 mb-2">
                        <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2 py-1 rounded-md flex-shrink-0">
                          Q{response.question_number}
                        </span>
                        <p className="text-sm text-gray-700 font-medium">
                          {response.question}
                        </p>
                      </div>
                      <p className="text-gray-900 font-semibold pl-2 border-l-2 border-emerald-200">
                        {Array.isArray(response.answer) ? response.answer.join(', ') : response.answer}
                      </p>
                      <div className={`flex items-center gap-1 mt-3 transition-opacity ${isEditingDisabled ? 'opacity-0' : 'opacity-0 group-hover:opacity-100'}`}>
                        <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                        <p className="text-xs text-yellow-700 font-medium">
                          {isEditingDisabled ? 'Editing disabled' : 'Click to edit and branch from here'}
                        </p>
                      </div>
                    </div>
                    )
                  })
                ) : (
                  <div className="p-6 bg-white/20 backdrop-blur-sm border-2 border-dashed border-white/40 rounded-xl">
                    <div className="flex items-center gap-2 text-white/90">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <p className="text-sm italic">
                        Your answered questions will appear here as you progress...
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Survey Completed - Generating Reviews */}
              {surveySession && surveySession.status === 'survey_completed' && isGeneratingReviews && (
                <div className="mt-6 p-6 bg-blue-50 border-2 border-blue-500 rounded-lg">
                  <div className="flex items-center gap-3">
                    <svg className="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <div>
                      <h3 className="text-xl font-bold text-blue-900">Survey Complete!</h3>
                      <p className="text-sm text-blue-700 mt-1">
                        Generating review options based on your responses...
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
            </div>
            </div>
          )}
        </div>
      )}

      {/* Review Pane (4th Pane - Rightmost) */}
      {showReviewPane && (
        <div
          ref={reviewPaneRef}
          onClick={activePaneIn4PaneMode !== 'review' ? () => {
            setActivePaneIn4PaneMode('review')
            setTimeout(() => reviewPaneRef.current?.scrollTo({ top: 0, behavior: 'smooth' }), 100)
          } : undefined}
          className={`transition-all duration-500 ${getReviewPaneWidth()} ${
            activePaneIn4PaneMode !== 'review'
              ? 'bg-purple-50'
              : 'bg-gradient-to-br from-purple-50 to-purple-100'
          } overflow-y-auto ${
            activePaneIn4PaneMode !== 'review'
              ? 'cursor-pointer hover:shadow-lg flex items-center justify-center relative'
              : 'p-8'
          }`}
        >
          {activePaneIn4PaneMode !== 'review' ? (
            <div className="fixed top-4 flex flex-col items-center w-full z-10">
              <div className="transform -rotate-90 origin-center whitespace-nowrap text-xs font-semibold text-purple-900 mt-12">
                Review
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl font-bold text-gray-900 mb-6">
                Review Options
              </h2>

              {/* Sentiment Band Indicator */}
              {sentimentBand && (
                <div className={`mb-6 p-4 rounded-lg border-2 ${
                  sentimentBand === 'good' ? 'bg-green-50 border-green-500' :
                  sentimentBand === 'okay' ? 'bg-yellow-50 border-yellow-500' :
                  'bg-red-50 border-red-500'
                }`}>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900">Survey Sentiment:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      sentimentBand === 'good' ? 'bg-green-200 text-green-900' :
                      sentimentBand === 'okay' ? 'bg-yellow-200 text-yellow-900' :
                      'bg-red-200 text-red-900'
                    }`}>
                      {sentimentBand.toUpperCase()}
                    </span>
                  </div>
                </div>
              )}

              {/* Loading State */}
              {isGeneratingReviews && (
                <div className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <svg className="animate-spin h-12 w-12 text-purple-600 mx-auto mb-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <p className="text-gray-600">Generating intelligent review options...</p>
                  </div>
                </div>
              )}

              {/* Error State */}
              {surveyError && !isGeneratingReviews && (
                <div className="p-6 bg-red-50 border-l-4 border-red-500 rounded-lg mb-6">
                  <p className="text-sm text-red-700 mb-2">
                    <strong>Error:</strong> {surveyError}
                  </p>
                  <button
                    onClick={() => surveySession && generateReviews(surveySession.session_id)}
                    className="text-sm text-red-600 underline hover:text-red-800"
                  >
                    Try again
                  </button>
                </div>
              )}

              {/* Review Options */}
              {!isGeneratingReviews && reviewOptions.length > 0 && (
                <>
                  <div className="mb-4 flex items-center justify-between">
                    <p className="text-sm text-gray-600">
                      {isReviewSubmitted ? 'Review submitted successfully!' : 'Select the review that best matches your experience:'}
                    </p>
                    <button
                      onClick={regenerateReviews}
                      disabled={isGeneratingReviews || isReviewSubmitted}
                      className="text-sm bg-purple-100 hover:bg-purple-200 text-purple-800 px-4 py-2 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Refresh Reviews
                    </button>
                  </div>

                  <div className="space-y-4">
                    {reviewOptions.map((review, idx) => (
                      <div
                        key={idx}
                        onClick={() => !isReviewSubmitted && setSelectedReviewIndex(idx)}
                        className={`border-2 rounded-lg p-5 transition-all ${
                          isReviewSubmitted ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'
                        } ${
                          selectedReviewIndex === idx
                            ? 'border-purple-600 bg-purple-50 shadow-lg'
                            : isReviewSubmitted
                            ? 'border-gray-300 bg-gray-50'
                            : 'border-gray-300 hover:border-purple-400 hover:shadow-md bg-white'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <span className="font-semibold text-gray-900 text-lg">Option {idx + 1}</span>
                            <div className="flex items-center">
                              {[...Array(5)].map((_, i) => (
                                <svg
                                  key={i}
                                  className={`w-5 h-5 ${i < review.review_stars ? 'text-yellow-400' : 'text-gray-300'}`}
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                                </svg>
                              ))}
                            </div>
                          </div>
                          {selectedReviewIndex === idx && (
                            <div className="bg-purple-600 text-white px-3 py-1 rounded-full text-xs font-medium">
                              Selected
                            </div>
                          )}
                        </div>

                        <p className="text-gray-700 leading-relaxed mb-3">
                          {review.review_text}
                        </p>

                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                            Tone: {review.tone}
                          </span>
                          {review.highlights && review.highlights.length > 0 && (
                            <>
                              {review.highlights.map((highlight, hidx) => (
                                <span key={hidx} className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded">
                                  {highlight}
                                </span>
                              ))}
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Submit Button */}
                  {!isReviewSubmitted && (
                    <div className="mt-8">
                      <button
                        onClick={submitReview}
                        disabled={selectedReviewIndex === null || isLoadingSurvey}
                        className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-4 px-6 rounded-lg shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {isLoadingSurvey ? (
                          <span className="flex items-center justify-center gap-2">
                            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                            </svg>
                            Submitting Review...
                          </span>
                        ) : (
                          'Submit Selected Review'
                        )}
                      </button>
                    </div>
                  )}
                </>
              )}

              {/* Review Submitted Confirmation */}
              {surveySession && surveySession.status === 'completed' && (
                <div className="p-6 bg-green-50 border-2 border-green-500 rounded-lg">
                  <div className="flex items-center gap-3">
                    <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <h3 className="text-xl font-bold text-green-900">Review Submitted!</h3>
                      <p className="text-sm text-green-700 mt-1">
                        Thank you for completing the survey and submitting your review.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </main>
  )
}
