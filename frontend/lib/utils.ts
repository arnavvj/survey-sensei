import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function generateMockEmail(name: string): string {
  const sanitized = name.toLowerCase().replace(/\s+/g, '.')
  const suffix = Math.floor(Math.random() * 10000)
  return `${sanitized}.${suffix}@example.com`
}

export function generateRandomAge(min = 18, max = 75): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function generateRandomZip(): string {
  return String(Math.floor(Math.random() * 90000) + 10000)
}

export const US_CITIES = [
  { city: 'New York', state: 'NY' },
  { city: 'Los Angeles', state: 'CA' },
  { city: 'Chicago', state: 'IL' },
  { city: 'Houston', state: 'TX' },
  { city: 'Phoenix', state: 'AZ' },
  { city: 'Philadelphia', state: 'PA' },
  { city: 'San Antonio', state: 'TX' },
  { city: 'San Diego', state: 'CA' },
  { city: 'Dallas', state: 'TX' },
  { city: 'San Jose', state: 'CA' },
  { city: 'Austin', state: 'TX' },
  { city: 'Jacksonville', state: 'FL' },
  { city: 'Fort Worth', state: 'TX' },
  { city: 'Columbus', state: 'OH' },
  { city: 'Charlotte', state: 'NC' },
  { city: 'San Francisco', state: 'CA' },
  { city: 'Indianapolis', state: 'IN' },
  { city: 'Seattle', state: 'WA' },
  { city: 'Denver', state: 'CO' },
  { city: 'Boston', state: 'MA' },
]

export function getRandomCity() {
  return US_CITIES[Math.floor(Math.random() * US_CITIES.length)]
}

export const MOCK_NAMES = {
  male: [
    'James Smith', 'Robert Williams', 'Michael Jones', 'David Rodriguez',
    'William Miller', 'Richard Hernandez', 'Joseph Gonzalez', 'Thomas Anderson',
    'Christopher Moore', 'Charles Martin', 'Daniel White', 'Matthew Harris',
    'Raj Patel', 'Wei Chen', 'Muhammad Ali', 'Carlos Garcia',
    'Hiroshi Tanaka', 'Ahmed Hassan', 'Liam O\'Brien', 'Marco Rossi',
    'Yuki Yamamoto', 'Diego Santos', 'Ivan Petrov', 'Jean Dubois'
  ],
  female: [
    'Mary Johnson', 'Patricia Brown', 'Jennifer Garcia', 'Linda Davis',
    'Barbara Martinez', 'Susan Lopez', 'Jessica Wilson', 'Sarah Taylor',
    'Karen Jackson', 'Nancy Lee', 'Lisa Anderson', 'Betty Thomas',
    'Priya Sharma', 'Mei Wang', 'Fatima Khan', 'Maria Rodriguez',
    'Yuki Sato', 'Amina Ibrahim', 'Emma Murphy', 'Sofia Rossi',
    'Hana Kim', 'Ana Silva', 'Olga Ivanova', 'Claire Martin'
  ]
}

export function getRandomName(gender?: 'Male' | 'Female'): string {
  if (gender === 'Male') {
    return MOCK_NAMES.male[Math.floor(Math.random() * MOCK_NAMES.male.length)]
  } else if (gender === 'Female') {
    return MOCK_NAMES.female[Math.floor(Math.random() * MOCK_NAMES.female.length)]
  } else {
    // Random gender if not specified
    const allNames = [...MOCK_NAMES.male, ...MOCK_NAMES.female]
    return allNames[Math.floor(Math.random() * allNames.length)]
  }
}

export function getGenderFromName(name: string): 'Male' | 'Female' {
  if (MOCK_NAMES.male.includes(name)) {
    return 'Male'
  } else if (MOCK_NAMES.female.includes(name)) {
    return 'Female'
  } else {
    // Default fallback
    return Math.random() > 0.5 ? 'Male' : 'Female'
  }
}

export function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}
