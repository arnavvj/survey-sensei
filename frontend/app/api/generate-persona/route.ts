import { NextRequest, NextResponse } from 'next/server'
import { getRandomName, getRandomCity, generateMockEmail, generateRandomAge, generateRandomZip } from '@/lib/utils'

// In-memory cache for tracking last generated gender (simple session-less approach)
// Key: will use a simple counter approach - alternates automatically
let lastGender: 'Male' | 'Female' | null = null

export async function POST(request: NextRequest) {
  try {
    // Accept optional lastGender from client
    const body = await request.json().catch(() => ({}))
    const clientLastGender = body.lastGender as 'Male' | 'Female' | null | undefined

    // Use client's lastGender if provided, otherwise use server-side tracking
    const previousGender = clientLastGender !== undefined ? clientLastGender : lastGender

    // Round-robin alternating gender
    let gender: 'Male' | 'Female'

    if (previousGender === null) {
      // First generation - random
      gender = Math.random() > 0.5 ? 'Male' : 'Female'
    } else {
      // Alternate from last gender
      gender = previousGender === 'Male' ? 'Female' : 'Male'
    }

    // Generate persona using diverse name list
    const name = getRandomName(gender)
    const city = getRandomCity()
    const age = generateRandomAge()

    const persona = {
      name,
      email: generateMockEmail(name),
      age,
      city: city.city,
      state: city.state,
      zip: generateRandomZip(),
      gender,
      location: `${city.city}, ${city.state}`,
    }

    // Update server-side cache
    lastGender = gender

    return NextResponse.json({
      success: true,
      persona,
    })
  } catch (error: any) {
    console.error('Error generating persona:', error)
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Failed to generate persona',
      },
      { status: 500 }
    )
  }
}
