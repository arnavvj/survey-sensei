/**
 * API Route: Generate Reviews
 * Proxies request to Python backend to generate review options using Agent 4
 */

import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Forward request to Python backend
    const response = await fetch(`${BACKEND_URL}/api/reviews/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || 'Failed to generate reviews' },
        { status: response.status }
      )
    }

    const data = await response.json()

    return NextResponse.json(data, { status: 200 })
  } catch (error: any) {
    console.error('Error generating reviews:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
