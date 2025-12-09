import { NextRequest, NextResponse } from 'next/server'
import { ProductData } from '@/lib/types'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

// Helper function to extract ASIN from any Amazon URL format
function extractASIN(url: string): string | null {
  const patterns = [
    // Standard product pages
    /\/dp\/([A-Z0-9]{10})/i,
    /\/gp\/product\/([A-Z0-9]{10})/i,
    /\/ASIN\/([A-Z0-9]{10})/i,
    // URLs with query parameters
    /\/dp\/([A-Z0-9]{10})[?&]/i,
    /\/gp\/product\/([A-Z0-9]{10})[?&]/i,
    // Product detail pages with ref=
    /\/([A-Z0-9]{10})\/ref=/i,
    // ASIN in query parameters
    /[?&]asin=([A-Z0-9]{10})/i,
    // Shortened amzn.to links
    /amzn\.to\/([A-Z0-9]{10})/i,
    // ASIN at end of path
    /\/([A-Z0-9]{10})$/i,
  ]

  for (const pattern of patterns) {
    const match = url.match(pattern)
    if (match && match[1]) {
      const asin = match[1].toUpperCase()
      if (/^[A-Z0-9]{10}$/.test(asin)) {
        return asin
      }
    }
  }

  return null
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url, mock = false } = body

    if (!url) {
      return NextResponse.json(
        { success: false, error: 'Product URL is required' },
        { status: 400 }
      )
    }

    // Check if mock mode
    const urlLower = url.toLowerCase().trim()
    const isMockMode = mock || urlLower.endsWith('/mock') || urlLower.endsWith('mock') || urlLower === 'mock'

    if (isMockMode) {
      console.log('🎭 Mock mode detected - returning test data')
      return NextResponse.json({
        success: true,
        data: {
          url: 'https://www.amazon.com/dp/MOCKTEST01',
          title: 'Mock Test Product - Premium Wireless Headphones with Noise Cancellation',
          price: 149.99,
          images: [
            'https://via.placeholder.com/600x600/4F46E5/FFFFFF?text=Mock+Product+1',
            'https://via.placeholder.com/600x600/7C3AED/FFFFFF?text=Mock+Product+2',
            'https://via.placeholder.com/600x600/EC4899/FFFFFF?text=Mock+Product+3'
          ],
          description: 'This is mock test data for development and testing purposes. Premium quality wireless headphones with active noise cancellation, 30-hour battery life, and comfortable over-ear design. Perfect for testing the Survey Sensei application without making real API calls.',
          brand: 'MockBrand Electronics',
          rating: 4.5,
          reviewCount: 1247,
          reviews: [],
          platform: 'amazon'
        }
      })
    }

    // Validate Amazon URL
    try {
      const parsed = new URL(url)
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        throw new Error('Invalid protocol')
      }
      if (!parsed.hostname.toLowerCase().includes('amazon')) {
        return NextResponse.json(
          { success: false, error: 'Only Amazon product URLs are supported. Please use amazon.com URLs.' },
          { status: 400 }
        )
      }
    } catch {
      return NextResponse.json(
        { success: false, error: 'Invalid URL format' },
        { status: 400 }
      )
    }

    // Extract ASIN
    const asin = extractASIN(url)
    if (!asin) {
      return NextResponse.json(
        { success: false, error: 'Could not extract ASIN from URL. Make sure the URL contains a valid Amazon product ID.' },
        { status: 400 }
      )
    }

    console.log(`📦 Extracted ASIN: ${asin} from URL`)

    // Call backend product preview endpoint (uses RapidAPI with caching)
    const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'
    console.log(`🔄 Fetching product from backend: ${BACKEND_URL}/api/product/preview`)

    const backendResponse = await fetch(`${BACKEND_URL}/api/product/preview`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ asin }),
    })

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}))
      throw new Error(errorData.error || `Backend error: ${backendResponse.status}`)
    }

    const backendData = await backendResponse.json()

    if (!backendData.success || !backendData.product) {
      throw new Error(backendData.error || 'Product not found')
    }

    const product = backendData.product

    console.log(`✅ Successfully fetched product from backend: ${product.title}`)

    // Transform backend response to frontend format
    const productData: ProductData = {
      url: product.product_url || url,
      title: product.title || 'Unknown Product',
      price: product.price,
      images: product.photos || [],
      description: product.description || product.title || '',
      brand: product.brand,
      rating: product.star_rating,
      reviewCount: product.num_ratings,
      reviews: [], // Reviews fetched separately during form submission
      platform: 'amazon',
    }

    return NextResponse.json({
      success: true,
      data: productData,
    })
  } catch (error: any) {
    console.error('❌ Scrape error:', error)
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Failed to fetch product. Please check the URL and try again.'
      },
      { status: 500 }
    )
  }
}
