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

    def generate_embeddings_batch(
        self,
        items: List[Dict[str, Any]],
        text_builder_fn,
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple items in batches (OPTIMIZED)

        This method is much more efficient than calling generate_single_embedding()
        for each item individually. OpenAI's API supports batching up to 2048 texts
        in a single call, which dramatically reduces API overhead.

        Args:
            items: List of items (products, users, or reviews)
            text_builder_fn: Function to build embedding text from item
            batch_size: Number of items to process in each API call (max 2048)

        Returns:
            Same list of items with 'embeddings' field populated
        """
        if not items:
            return items

        # Build all embedding texts first
        texts = []
        for item in items:
            try:
                text = text_builder_fn(item)
                texts.append(text)
            except Exception as e:
                logger.warning(f"Failed to build embedding text for item: {e}")
                texts.append("")  # Placeholder for failed items

        # Generate embeddings in batches
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                logger.info(f"Generating embeddings batch {batch_num}/{total_batches} ({len(batch_texts)} items)")
                batch_embeddings = self.generate_embeddings(batch_texts)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {batch_num}: {e}")
                # Add None embeddings for failed batch
                all_embeddings.extend([None] * len(batch_texts))

        # Assign embeddings back to items
        for item, embedding in zip(items, all_embeddings):
            item['embeddings'] = embedding

        return items

    # ============================================================================
    # Entity-specific embedding text builders
    # ============================================================================

    def build_product_embedding_text(self, product: Dict[str, Any]) -> str:
        """
        Build rich text representation of product for embedding generation

        Uses fields: item_id, title, brand, description, star_rating, num_ratings, category, price

        Args:
            product: Product dictionary

        Returns:
            Formatted text for embedding
        """
        parts = []

        if product.get('item_id'):
            parts.append(f"Product ID: {product['item_id']}")
        if product.get('title'):
            parts.append(f"Title: {product['title']}")
        if product.get('brand'):
            parts.append(f"Brand: {product['brand']}")
        if product.get('description'):
            parts.append(f"Description: {product['description']}")
        if product.get('category'):
            parts.append(f"Category: {product['category']}")
        if product.get('price'):
            parts.append(f"Price: ${product['price']:.2f}")
        if product.get('star_rating'):
            parts.append(f"Rating: {product['star_rating']}/5 stars")
        if product.get('num_ratings'):
            parts.append(f"Reviews: {product['num_ratings']}")

        return " | ".join(parts)

    def build_review_embedding_text(self, review: Dict[str, Any]) -> str:
        """
        Build rich text representation of review for embedding generation

        Uses fields: item_id, user_id, transaction_id, timestamp, review_title, review_text, review_stars

        Args:
            review: Review dictionary

        Returns:
            Formatted text for embedding
        """
        parts = []

        if review.get('item_id'):
            parts.append(f"Product: {review['item_id']}")
        if review.get('user_id'):
            parts.append(f"User: {review['user_id']}")
        if review.get('transaction_id'):
            parts.append(f"Transaction: {review['transaction_id']}")
        if review.get('timestamp'):
            parts.append(f"Date: {review['timestamp']}")
        if review.get('review_stars'):
            parts.append(f"Rating: {review['review_stars']}/5 stars")
        if review.get('review_title'):
            parts.append(f"Title: {review['review_title']}")
        if review.get('review_text'):
            parts.append(f"Review: {review['review_text']}")

        return " | ".join(parts)

    def build_user_embedding_text(self, user: Dict[str, Any]) -> str:
        """
        Build rich text representation of user profile for embedding generation

        Uses fields: user_name, age, base_location, base_zip, gender

        Args:
            user: User dictionary

        Returns:
            Formatted text for embedding
        """
        parts = []

        if user.get('user_name'):
            parts.append(f"Name: {user['user_name']}")
        if user.get('age'):
            parts.append(f"Age: {user['age']} years old")
        if user.get('gender'):
            parts.append(f"Gender: {user['gender']}")
        if user.get('base_location'):
            parts.append(f"Location: {user['base_location']}")
        if user.get('base_zip'):
            parts.append(f"ZIP: {user['base_zip']}")

        return " | ".join(parts)
