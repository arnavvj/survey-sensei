"""
MOCK_RVW_MINI_AGENT - Review Mock Data Generator
Generates realistic product reviews based on RapidAPI templates and agent generation
Uses gpt-4o-mini for cost-effective review generation
"""

from typing import List, Dict, Any
import random
import uuid
from datetime import datetime
from .base import BaseMockAgent


class MockReviewAgent(BaseMockAgent):
    """
    Generates mock reviews using:
    1. RapidAPI review templates (if available)
    2. Agent-generated reviews for variation
    """

    def generate_reviews_from_api_templates(
        self,
        api_reviews: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        product_id: str
    ) -> List[Dict[str, Any]]:
        """
        Convert RapidAPI review templates to database format

        Args:
            api_reviews: Reviews from RapidAPI with fields:
                - review_title
                - review_comment (maps to review_text)
                - review_star_rating
                - reviewer_name
            transactions: Available transactions for this product
            product_id: Product ASIN

        Returns:
            List of review dictionaries
        """
        reviews = []

        # Match API reviews with transactions
        available_transactions = [
            t for t in transactions
            if t['item_id'] == product_id and t['transaction_status'] == 'delivered'
        ]

        for api_review, transaction in zip(api_reviews, available_transactions[:len(api_reviews)]):
            review = {
                'review_id': str(uuid.uuid4()),
                'item_id': transaction['item_id'],
                'user_id': transaction['user_id'],
                'transaction_id': transaction['transaction_id'],
                'timestamp': transaction['delivery_date'],  # Review after delivery
                'review_title': api_review.get('review_title', 'Great product'),
                'review_text': api_review.get('review_comment', 'Good quality product.'),
                'review_stars': int(api_review.get('review_star_rating', 5)),
                'source': 'rapidapi',  # Template from API
                'manual_or_agent_generated': 'agent',  # Legacy field
                'embeddings': None,  # Reserved for future
                'is_mock': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
            }
            reviews.append(review)

        return reviews

    def generate_agent_reviews(
        self,
        product: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate reviews using LLM for transactions without RapidAPI templates

        Args:
            product: Product dictionary
            transactions: Available transactions for this product
            count: Number of reviews to generate

        Returns:
            List of review dictionaries
        """
        # Filter delivered transactions that need reviews
        available_transactions = [
            t for t in transactions
            if t['item_id'] == product['item_id'] and t['transaction_status'] == 'delivered'
        ]

        if not available_transactions:
            return []

        # Generate reviews in batches to save LLM calls
        reviews = []
        batch_size = 5  # Generate 5 reviews per LLM call

        for i in range(0, min(count, len(available_transactions)), batch_size):
            batch_count = min(batch_size, count - i, len(available_transactions) - i)

            system_prompt = """You are a review generator creating realistic product reviews.
Generate diverse reviews with varying:
- Star ratings (1-5, with realistic distribution: mostly 4-5 stars, some 3, few 1-2)
- Review lengths (some brief, some detailed)
- Tones (positive, neutral, critical based on rating)
- Focus areas (quality, value, shipping, features)

Return ONLY valid JSON."""

            user_prompt = f"""Generate {batch_count} realistic reviews for this product:

Product: {product['title']}
Brand: {product.get('brand', 'Unknown')}
Price: ${product.get('price', 0):.2f}

Return JSON array:
[
  {{
    "review_title": "brief title (3-8 words)",
    "review_text": "review body (2-4 sentences)",
    "review_stars": rating 1-5 as integer
  }}
]

Make them realistic and varied."""

            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
                temperature=0.9
            )

            generated_reviews = self._parse_json_response(response)

            # Ensure it's a list
            if isinstance(generated_reviews, dict):
                generated_reviews = [generated_reviews]

            # Match with transactions
            for j, review_data in enumerate(generated_reviews):
                if i + j >= len(available_transactions):
                    break

                transaction = available_transactions[i + j]

                review = {
                    'review_id': str(uuid.uuid4()),
                    'item_id': transaction['item_id'],
                    'user_id': transaction['user_id'],
                    'transaction_id': transaction['transaction_id'],
                    'timestamp': transaction['delivery_date'],
                    'review_title': review_data['review_title'],
                    'review_text': review_data['review_text'],
                    'review_stars': review_data['review_stars'],
                    'source': 'agent_generated',
                    'manual_or_agent_generated': 'agent',
                    'embeddings': None,
                    'is_mock': True,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                }
                reviews.append(review)

        return reviews[:count]
