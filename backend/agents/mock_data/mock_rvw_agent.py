"""
MOCK_RVW_MINI_AGENT - Review Mock Data Generator
Generates realistic product reviews with proper sentiment distribution
Includes original RapidAPI reviews + generated reviews
Uses gpt-4o-mini for cost-effective review generation
"""

from typing import List, Dict, Any, Tuple
import random
import uuid
from datetime import datetime
from .base import BaseMockAgent
from .mock_trx_agent import MockTransactionAgent


class MockReviewAgent(BaseMockAgent):
    """
    Generates mock reviews following workflow:
    1. Convert RapidAPI reviews to DB format (original data first!)
    2. Generate additional reviews for sentiment spread
    3. Generate reviews for similar products
    4. Generate main user reviews
    """

    def __init__(self):
        super().__init__()
        self.trx_agent = MockTransactionAgent()

    def convert_api_reviews_to_db_format(
        self,
        api_reviews: List[Dict[str, Any]],
        transactions: List[Dict[str, Any]],
        main_product: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Convert ORIGINAL RapidAPI reviews to database format
        These are the real scraped reviews that must be included first!

        Args:
            api_reviews: Reviews from RapidAPI
            transactions: Corresponding transactions (already created)
            main_product: Main product dictionary

        Returns:
            List of review dictionaries in DB format
        """
        reviews = []

        for api_review, transaction in zip(api_reviews, transactions):
            review = {
                'review_id': str(uuid.uuid4()),
                'item_id': main_product['item_id'],
                'user_id': transaction['user_id'],
                'transaction_id': transaction['transaction_id'],
                'timestamp': transaction['delivery_date'],
                'review_title': api_review.get('review_title', 'Great product'),
                'review_text': api_review.get('review_comment', 'Good quality product.'),
                'review_stars': int(api_review.get('review_star_rating', 5)),
                'source': 'rapidapi',  # Scraped from Amazon via RapidAPI
                'manual_or_agent_generated': 'manual',  # Human-written review text
                'embeddings': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
            }
            reviews.append(review)

        return reviews

    def generate_reviews_for_sentiment_spread(
        self,
        main_product: Dict[str, Any],
        mock_users: List[Dict[str, Any]],
        existing_reviews: List[Dict[str, Any]],
        sentiment_spread: Dict[str, int],
        target_total: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate additional reviews to meet sentiment spread requirements

        Args:
            main_product: Main product dictionary
            mock_users: List of mock users
            existing_reviews: Already created reviews (from RapidAPI)
            sentiment_spread: {'good': 70, 'neutral': 20, 'bad': 10}
            target_total: Total reviews needed (e.g., 100)

        Returns:
            Tuple of (reviews, transactions)
        """
        # Calculate current sentiment distribution
        current_count = len(existing_reviews)
        needed_count = target_total - current_count

        if needed_count <= 0:
            return [], []

        # Calculate how many of each sentiment needed
        good_needed = int((sentiment_spread['good'] / 100) * target_total) - len([r for r in existing_reviews if r['review_stars'] >= 4])
        neutral_needed = int((sentiment_spread['neutral'] / 100) * target_total) - len([r for r in existing_reviews if r['review_stars'] == 3])
        bad_needed = int((sentiment_spread['bad'] / 100) * target_total) - len([r for r in existing_reviews if r['review_stars'] <= 2])

        # Ensure we generate exactly needed_count reviews
        good_needed = max(0, good_needed)
        neutral_needed = max(0, neutral_needed)
        bad_needed = max(0, bad_needed)

        # Adjust if total doesn't match
        total_sentiment = good_needed + neutral_needed + bad_needed
        if total_sentiment < needed_count:
            good_needed += (needed_count - total_sentiment)

        reviews = []
        transactions = []

        # Generate good reviews (4-5 stars)
        if good_needed > 0:
            good_reviews, good_txns = self._generate_reviews_with_sentiment(
                product=main_product,
                users=mock_users,
                count=good_needed,
                sentiment='good'
            )
            reviews.extend(good_reviews)
            transactions.extend(good_txns)

        # Generate neutral reviews (3 stars)
        if neutral_needed > 0:
            neutral_reviews, neutral_txns = self._generate_reviews_with_sentiment(
                product=main_product,
                users=mock_users,
                count=neutral_needed,
                sentiment='neutral'
            )
            reviews.extend(neutral_reviews)
            transactions.extend(neutral_txns)

        # Generate bad reviews (1-2 stars)
        if bad_needed > 0:
            bad_reviews, bad_txns = self._generate_reviews_with_sentiment(
                product=main_product,
                users=mock_users,
                count=bad_needed,
                sentiment='bad'
            )
            reviews.extend(bad_reviews)
            transactions.extend(bad_txns)

        return reviews, transactions

    def _generate_reviews_with_sentiment(
        self,
        product: Dict[str, Any],
        users: List[Dict[str, Any]],
        count: int,
        sentiment: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Generate reviews with specific sentiment (batched for large counts)"""
        reviews = []
        transactions = []

        # Generate in batches of 10 to avoid token limits
        batch_size = 10
        remaining = count

        while remaining > 0:
            batch_count = min(batch_size, remaining)

            system_prompt = f"""You are a review generator creating realistic {sentiment} product reviews.

Sentiment Guidelines:
- good: 4-5 stars, positive tone, praise features/quality/value
- neutral: 3 stars, mixed feelings, "it's okay" tone
- bad: 1-2 stars, critical tone, mention issues/disappointment

Return ONLY valid JSON."""

            user_prompt = f"""Generate {batch_count} {sentiment} reviews for this product:

Product: {product['title']}
Brand: {product.get('brand', 'Unknown')}
Price: ${product.get('price', 0):.2f}

Return JSON array:
[
  {{
    "review_title": "brief title (3-8 words)",
    "review_text": "review body (2-4 sentences, {sentiment} tone)",
    "review_stars": rating (good=4-5, neutral=3, bad=1-2)
  }}
]"""

            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=800,
                temperature=0.9
            )

            generated_reviews_data = self._parse_json_response(response)
            if isinstance(generated_reviews_data, dict):
                generated_reviews_data = [generated_reviews_data]

            for review_data in generated_reviews_data[:batch_count]:
                user = random.choice(users)

                # Create transaction first
                transaction = self.trx_agent.create_transaction_for_review(
                    user=user,
                    product=product
                )
                transactions.append(transaction)

                # Create review
                review = {
                    'review_id': str(uuid.uuid4()),
                    'item_id': product['item_id'],
                    'user_id': user['user_id'],
                    'transaction_id': transaction['transaction_id'],
                    'timestamp': transaction['delivery_date'],
                    'review_title': review_data['review_title'],
                    'review_text': review_data['review_text'],
                    'review_stars': review_data['review_stars'],
                    'source': 'agent_generated',  # Generated by MOCK_RVW_MINI_AGENT
                    'manual_or_agent_generated': 'agent',  # AI-generated review text
                    'embeddings': None,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                }
                reviews.append(review)

            remaining -= batch_count

        return reviews, transactions

    def generate_reviews_for_similar_products(
        self,
        similar_products: List[Dict[str, Any]],
        mock_users: List[Dict[str, Any]],
        reviews_per_product: int = 20
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate reviews for similar products (random distribution)

        Args:
            similar_products: List of similar products
            mock_users: List of mock users
            reviews_per_product: How many reviews per product

        Returns:
            Tuple of (reviews, transactions)
        """
        all_reviews = []
        all_transactions = []

        for product in similar_products:
            # Random distribution for similar products
            reviews, transactions = self._generate_reviews_with_sentiment(
                product=product,
                users=mock_users,
                count=reviews_per_product,
                sentiment=random.choice(['good', 'good', 'good', 'neutral', 'bad'])  # Mostly positive
            )
            all_reviews.extend(reviews)
            all_transactions.extend(transactions)

        return all_reviews, all_transactions

    def generate_main_user_similar_reviews(
        self,
        main_user: Dict[str, Any],
        similar_products: List[Dict[str, Any]],
        count: int
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Generate main user's reviews for similar products

        Args:
            main_user: Main user dictionary
            similar_products: List of similar products
            count: Number of reviews to generate

        Returns:
            Tuple of (reviews, transactions)
        """
        selected_products = random.sample(similar_products, min(count, len(similar_products)))

        reviews = []
        transactions = []

        for product in selected_products:
            # Create transaction
            transaction = self.trx_agent.create_transaction_for_review(
                user=main_user,
                product=product
            )
            transaction['is_mock'] = False  # Main user transaction
            transactions.append(transaction)

            # Generate review
            system_prompt = """You are generating a realistic product review.
Make it personal, detailed, and authentic. Return ONLY valid JSON."""

            user_prompt = f"""Generate 1 review for:
Product: {product['title']}
Price: ${product.get('price', 0):.2f}

Return:
{{
  "review_title": "title",
  "review_text": "detailed review (3-5 sentences)",
  "review_stars": rating 1-5
}}"""

            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=300,
                temperature=0.8
            )

            review_data = self._parse_json_response(response)

            review = {
                'review_id': str(uuid.uuid4()),
                'item_id': product['item_id'],
                'user_id': main_user['user_id'],
                'transaction_id': transaction['transaction_id'],
                'timestamp': transaction['delivery_date'],
                'review_title': review_data['review_title'],
                'review_text': review_data['review_text'],
                'review_stars': review_data['review_stars'],
                'source': 'agent_generated',  # Generated for main user
                'manual_or_agent_generated': 'agent',  # AI-generated review text
                'embeddings': None,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
            }
            reviews.append(review)

        return reviews, transactions

    def generate_main_user_exact_review(
        self,
        main_user: Dict[str, Any],
        main_product: Dict[str, Any],
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate main user's review for exact product

        Args:
            main_user: Main user dictionary
            main_product: Main product dictionary
            transaction: Existing transaction

        Returns:
            Single review dictionary
        """
        system_prompt = """You are generating a detailed, authentic product review from a real customer.
Make it personal and specific. Return ONLY valid JSON."""

        user_prompt = f"""Generate 1 detailed review for:
Product: {main_product['title']}
Price: ${main_product.get('price', 0):.2f}

Return:
{{
  "review_title": "title",
  "review_text": "detailed personal review (4-6 sentences)",
  "review_stars": rating 1-5
}}"""

        response = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=400,
            temperature=0.8
        )

        review_data = self._parse_json_response(response)

        review = {
            'review_id': str(uuid.uuid4()),
            'item_id': main_product['item_id'],
            'user_id': main_user['user_id'],
            'transaction_id': transaction['transaction_id'],
            'timestamp': transaction['delivery_date'],
            'review_title': review_data['review_title'],
            'review_text': review_data['review_text'],
            'review_stars': review_data['review_stars'],
            'source': 'agent_generated',  # Generated for main user
            'manual_or_agent_generated': 'agent',  # AI-generated review text
            'embeddings': None,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        return review
