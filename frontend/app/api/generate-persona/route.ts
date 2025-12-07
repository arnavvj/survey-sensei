import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

export async function POST(request: NextRequest) {
  try {
    console.log('Generating user persona using Claude Haiku...')

    // Use Claude Haiku (cheap, fast) for persona generation
    const message = await anthropic.messages.create({
      model: 'claude-3-haiku-20240307',
      max_tokens: 500,
      temperature: 1.0, // High temperature for diversity
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

    const responseText = message.content[0].type === 'text' ? message.content[0].text : ''
    console.log('Raw response:', responseText)

    // Extract JSON from response (handle markdown code blocks)
    let jsonText = responseText.trim()
    if (jsonText.startsWith('```json')) {
      jsonText = jsonText.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim()
    } else if (jsonText.startsWith('```')) {
      jsonText = jsonText.replace(/```\n?/g, '').trim()
    }

    const persona = JSON.parse(jsonText)

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
