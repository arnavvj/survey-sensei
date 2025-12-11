import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function POST(request: NextRequest) {
  try {
    console.log('Generating user persona using GPT-4o-mini...')

    // Use GPT-4o-mini (cheap, fast) for persona generation
    const completion = await openai.chat.completions.create({
      model: 'gpt-4o-mini',
      max_tokens: 500,
      temperature: 1.0, // High temperature for diversity
      response_format: { type: 'json_object' },
      messages: [
        {
          role: 'user',
          content: `Generate a realistic, diverse Amazon customer persona.

Requirements:
- Name: Full name (diverse ethnic backgrounds, not just common American names)
- Email: Realistic email address based on name (various domains: gmail, yahoo, outlook, icloud, etc.)
- Age: Random between 18-75 (weighted towards 25-55 age range)
- Location: Any US city/town (include small towns, suburbs, not just major cities)
- State: Full state name (e.g., "California" not "CA")
- ZIP: Valid 5-digit US ZIP code matching the city/state
- Gender: Male or Female

Make it feel like a real person with natural combinations (name style matches ethnicity, email matches name/age, location is diverse).

Return ONLY valid JSON in this exact format:
{
  "name": "...",
  "email": "...",
  "age": ...,
  "city": "...",
  "state": "...",
  "zip": "...",
  "gender": "Male" or "Female"
}`,
        },
      ],
    })

    const responseText = completion.choices[0].message.content || '{}'
    console.log('Raw response:', responseText)

    // Parse JSON response (GPT-4o-mini with json_object mode returns pure JSON)
    const persona = JSON.parse(responseText)

    // Validate required fields
    const requiredFields = ['name', 'email', 'age', 'city', 'state', 'zip', 'gender']
    for (const field of requiredFields) {
      if (!persona[field]) {
        throw new Error(`Missing required field: ${field}`)
      }
    }

    // Validate types
    if (typeof persona.age !== 'number' || persona.age < 18 || persona.age > 75) {
      throw new Error('Invalid age')
    }
    if (!['Male', 'Female'].includes(persona.gender)) {
      throw new Error('Invalid gender')
    }
    if (!/^\d{5}$/.test(persona.zip)) {
      throw new Error('Invalid ZIP code format')
    }

    // Add location field (for backward compatibility)
    persona.location = `${persona.city}, ${persona.state}`

    console.log('Generated persona:', persona)

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
