/**
 * OpenAI Embeddings Utility
 * Generates real embeddings using OpenAI API
 */

import OpenAI from 'openai'

// Initialize OpenAI client
const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

const EMBEDDING_MODEL = 'text-embedding-3-small'
const EMBEDDING_DIMENSIONS = 1536

/**
 * Generate embedding for a single text
 * @param text - Text to embed
 * @returns 1536-dimensional embedding vector
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  try {
    const response = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: text,
      encoding_format: 'float',
    })

    return response.data[0].embedding
  } catch (error: any) {
    console.error('Error generating embedding:', error)
    throw new Error(`Failed to generate embedding: ${error.message}`)
  }
}

/**
 * Generate embeddings for multiple texts in batch
 * More efficient than calling generateEmbedding multiple times
 * @param texts - Array of texts to embed
 * @returns Array of 1536-dimensional embedding vectors
 */
export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
  try {
    // OpenAI supports batch requests up to 2048 inputs
    if (texts.length > 2048) {
      throw new Error('Too many texts. Maximum 2048 texts per batch.')
    }

    const response = await openai.embeddings.create({
      model: EMBEDDING_MODEL,
      input: texts,
      encoding_format: 'float',
    })

    return response.data.map((item) => item.embedding)
  } catch (error: any) {
    console.error('Error generating embeddings:', error)
    throw new Error(`Failed to generate embeddings: ${error.message}`)
  }
}

/**
 * Generate embedding for product data
 * Combines title, description, and brand for comprehensive embedding
 */
export async function generateProductEmbedding(
  title: string,
  description: string,
  brand: string
): Promise<number[]> {
  const text = `${title} ${description} ${brand}`.trim()
  return generateEmbedding(text)
}

/**
 * Generate embedding for user data
 * Combines demographic information for user profiling
 */
export async function generateUserEmbedding(
  name: string,
  gender: string,
  age: number,
  location: string,
  creditScore: number,
  monthlyExpenses: number
): Promise<number[]> {
  const text = `${name} ${gender} age ${age} ${location} credit score ${creditScore} monthly expenses ${monthlyExpenses}`
  return generateEmbedding(text)
}

/**
 * Generate embedding for review data
 * Combines title and text for sentiment analysis
 */
export async function generateReviewEmbedding(
  title: string,
  text: string
): Promise<number[]> {
  const combined = `${title} ${text}`.trim()
  return generateEmbedding(combined)
}
