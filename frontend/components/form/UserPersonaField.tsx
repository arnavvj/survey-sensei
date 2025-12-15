'use client'

import { useState, useEffect } from 'react'
import { getRandomName, getRandomCity, generateMockEmail, generateRandomAge, generateRandomZip } from '@/lib/utils'

interface UserPersona {
  name: string
  email: string
  age: number
  location: string
  city: string
  state: string
  zip: string
  gender: 'Male' | 'Female'
}

interface Props {
  value?: UserPersona
  onChange: (value: UserPersona) => void
}

export function UserPersonaField({ value, onChange }: Props) {
  const [persona, setPersona] = useState<UserPersona | null>(value || null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [lastGender, setLastGender] = useState<'Male' | 'Female' | null>(null)

  // Generate persona using agent API (with fallback to helper functions)
  const generatePersona = async () => {
    setIsGenerating(true)

    try {
      // Try agent-based generation first
      const response = await fetch('/api/generate-persona', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        throw new Error('API request failed')
      }

      const result = await response.json()

      if (result.success && result.persona) {
        setPersona(result.persona)
        setLastGender(result.persona.gender)
        // Silent - no console logging
      } else {
        throw new Error(result.error || 'Failed to generate persona')
      }
    } catch (err: any) {
      // Silent fallback - no console warnings

      // Fallback to helper functions if API fails
      // Round-robin alternating gender with randomization
      let gender: 'Male' | 'Female'

      if (lastGender === null) {
        // First generation - random
        gender = Math.random() > 0.5 ? 'Male' : 'Female'
      } else {
        // Alternate from last gender
        gender = lastGender === 'Male' ? 'Female' : 'Male'
      }

      const name = getRandomName(gender)
      const city = getRandomCity()
      const age = generateRandomAge()

      const fallbackPersona: UserPersona = {
        name,
        email: generateMockEmail(name),
        age,
        location: `${city.city}, ${city.state}`,
        city: city.city,
        state: city.state,
        zip: generateRandomZip(),
        gender,
      }

      setPersona(fallbackPersona)
      setLastGender(gender)
      // Silent - no console logging
    } finally {
      setIsGenerating(false)
    }
  }

  useEffect(() => {
    if (!persona) {
      generatePersona()
    }
  }, [persona])

  const handleContinue = () => {
    if (persona) {
      onChange(persona)
    }
  }

  const handleRegenerate = () => {
    setPersona(null) // Clear current persona to trigger regeneration
  }

  if (!persona) {
    return (
      <div className="card animate-slide-in">
        <div className="text-center py-8">
          <svg className="animate-spin h-8 w-8 mx-auto text-primary-600" viewBox="0 0 24 24">
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
          <p className="text-gray-600 mt-2">Generating user persona...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="card animate-slide-in">
      <label className="block text-lg font-semibold text-gray-800 mb-3">
        5. Simulated User Profile
      </label>
      <p className="text-sm text-gray-600 mb-4">
        This is the user persona for whom we'll generate a personalized survey.
      </p>

      <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-5 border border-purple-200">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">Name</label>
            <p className="text-gray-900 font-medium">{persona.name}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">Email</label>
            <p className="text-gray-900 font-medium text-sm break-all">{persona.email}</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">Age</label>
            <p className="text-gray-900 font-medium">{persona.age} years</p>
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase">Gender</label>
            <p className="text-gray-900 font-medium">{persona.gender}</p>
          </div>
          <div className="col-span-2">
            <label className="text-xs font-medium text-gray-500 uppercase">Location</label>
            <p className="text-gray-900 font-medium">
              {persona.city}, {persona.state} {persona.zip}
            </p>
          </div>
        </div>
      </div>

      <div className="flex gap-3 mt-4">
        <button
          onClick={handleRegenerate}
          disabled={isGenerating}
          className="btn-secondary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? 'Generating...' : 'Regenerate'}
        </button>
        <button
          onClick={handleContinue}
          disabled={isGenerating}
          className="btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Continue
        </button>
      </div>
    </div>
  )
}
