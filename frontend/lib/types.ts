import { z } from 'zod'

// Form state types
export type FormStep = 1 | 2 | 3 | 4 | 5 | 6 | 7

export interface ProductData {
  url: string
  title: string
  price?: number
  images: string[]
  description: string
  brand?: string
  rating?: number
  reviewCount?: number
  reviews?: ScrapedReview[]
  platform: string
}

export interface ScrapedReview {
  author: string
  rating: number
  title: string
  text: string
  date: string
  verified?: boolean
}

export interface FormData {
  // Field 1
  productUrl: string
  productData?: ProductData

  // Field 2
  hasReviews?: 'yes' | 'no'

  // Field 3 (if hasReviews = yes)
  sentimentSpread?: {
    good: number
    neutral: number
    bad: number
  }

  // Field 4 (if hasReviews = no)
  hasSimilarProductsReviewed?: 'yes' | 'no'

  // Field 5
  userPersona?: {
    name: string
    email: string
    age: number
    location: string
    city: string
    state: string
    zip: string
    gender: 'Male' | 'Female'
  }

  // Field 6
  userHasPurchasedSimilar?: 'yes' | 'no'

  // Field 7
  userHasPurchasedExact?: 'yes' | 'no'
}

export interface MockDataSummary {
  products: number
  users: number
  transactions: number
  reviews: number
  scenario: string
  coldStart: {
    product: boolean
    user: boolean
  }
}

// Validation schemas
export const productUrlSchema = z.string().url().refine(
  (url) => {
    try {
      const parsed = new URL(url)
      return ['http:', 'https:'].includes(parsed.protocol)
    } catch {
      return false
    }
  },
  { message: 'Must be a valid http(s) URL' }
)

export const sentimentSpreadSchema = z.object({
  good: z.number().min(0).max(100),
  neutral: z.number().min(0).max(100),
  bad: z.number().min(0).max(100),
}).refine(
  (data) => data.good + data.neutral + data.bad === 100,
  { message: 'Total must equal 100%' }
)

export const userPersonaSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email format'),
  age: z.number().int().min(13).max(120),
  location: z.string().min(1),
  city: z.string().min(1),
  state: z.string().min(1),
  zip: z.string().regex(/^\d{5}$/, 'Must be 5 digits'),
  gender: z.enum(['Male', 'Female']),
})

// API Response types
export interface ScrapeResponse {
  success: boolean
  data?: ProductData
  error?: string
}

export interface MockDataResponse {
  success: boolean
  summary?: MockDataSummary
  error?: string
}

export interface SubmitResponse {
  success: boolean
  scenarioId?: string
  error?: string
}

// Survey types
export interface SurveyQuestion {
  question_text: string
  options: string[]
  reasoning?: string
  question_type?: 'single' | 'multiple'
}

export interface SurveyResponse {
  question: string
  answer: string | string[]
  question_number: number
}

export interface SurveySession {
  session_id: string
  question?: SurveyQuestion
  question_number: number
  total_questions: number
  status?: 'continue' | 'completed'
  review_options?: ReviewOption[]
  responses: SurveyResponse[]
}

export interface ReviewOption {
  review_text: string
  rating: number
  sentiment: string
  tone: string
}
