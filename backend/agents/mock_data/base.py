"""
Base class for all MOCK_DATA_MINI_AGENTS
Provides cost-effective LLM configuration and common utilities
"""

from typing import Optional, Dict, Any, List
import time
import logging
from openai import OpenAI
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseMockAgent:
    """
    Base class for mock data generation agents
    Uses gpt-4o-mini for cost efficiency during data engineering phase
    Enhanced with embeddings, retry logic, and caching
    """

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        # Force use of cheapest model for data engineering
        self.model = "gpt-4o-mini"
        self.embedding_model = settings.embedding_model  # text-embedding-3-small
        self.temperature = 0.8  # Higher temperature for diversity in mock data
        self.max_tokens = 500  # Keep responses concise to save costs

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Cost-effective LLM call with minimal token usage and retry logic

        Args:
            system_prompt: System instructions
            user_prompt: User query
            temperature: Override default temperature
            max_tokens: Override default max tokens
            response_format: Optional JSON schema for structured output

        Returns:
            LLM response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        params = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        if response_format:
            params["response_format"] = response_format

        # Retry logic for API failures
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**params)
                return response.choices[0].message.content
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"LLM call failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"LLM call failed after {self.max_retries} attempts: {e}")
                    raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            # Attempt to extract JSON from markdown code blocks
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON from code block. Error: {e2}")
                    logger.error(f"Response preview (first 500 chars): {response[:500]}")
                    raise ValueError(f"Failed to parse JSON response: {e2}")
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e2:
                    logger.error(f"Failed to parse JSON from code block. Error: {e2}")
                    logger.error(f"Response preview (first 500 chars): {response[:500]}")
                    raise ValueError(f"Failed to parse JSON response: {e2}")
            logger.error(f"No JSON found in response. Error: {e}")
            logger.error(f"Response preview (first 500 chars): {response[:500]}")
            raise ValueError(f"Failed to parse JSON response: {e}")

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for text using cost-effective embedding model

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Retry logic for embeddings API
        for attempt in range(self.max_retries):
            try:
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )
                return [item.embedding for item in response.data]
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Embedding generation failed (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Embedding generation failed after {self.max_retries} attempts: {e}")
                    raise

    def generate_single_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else None
