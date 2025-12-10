"""
MOCK_TRX_MINI_AGENT - Transaction Mock Data Generator
Generates realistic purchase transactions following e-commerce sparsity patterns
Uses deterministic rules (no LLM) to minimize costs
"""

from typing import List, Dict, Any
import random
import uuid
from datetime import datetime, timedelta


class MockTransactionAgent:
    """
    Generates mock transactions using deterministic rules
    Follows proper e-commerce data sparsity:
    - Users purchase 10-35% of available products
    - 40-50% of transactions have reviews
    """

    def _create_transaction(
        self,
        user: Dict[str, Any],
        product: Dict[str, Any],
        days_ago: int,
        is_mock: bool = True
    ) -> Dict[str, Any]:
        """Create a single transaction with realistic details"""
        order_date = datetime.now() - timedelta(days=days_ago)
        delivery_date = order_date + timedelta(days=random.randint(2, 7))
        expected_delivery = order_date + timedelta(days=random.randint(3, 5))

        original_price = float(product.get('price', 0))
        # Apply random discount (0-20%)
        discount = random.uniform(0, 0.20)
        retail_price = original_price * (1 - discount)

        # Determine status
        status_weights = [
            ('delivered', 0.85),
            ('returned', 0.10),
            ('pending', 0.05)
        ]
        status = random.choices(
            [s for s, _ in status_weights],
            weights=[w for _, w in status_weights]
        )[0]

        return_date = None
        if status == 'returned':
            return_date = delivery_date + timedelta(days=random.randint(3, 14))

        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'item_id': product['item_id'],
            'user_id': user['user_id'],
            'order_date': order_date.isoformat(),
            'delivery_date': delivery_date.isoformat() if status == 'delivered' or status == 'returned' else None,
            'expected_delivery_date': expected_delivery.isoformat(),
            'return_date': return_date.isoformat() if return_date else None,
            'original_price': round(original_price, 2),
            'retail_price': round(retail_price, 2),
            'transaction_status': status,
            'is_mock': is_mock,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        return transaction

    # =========================================================================
    # NEW METHODS FOR REDESIGNED ORCHESTRATOR WORKFLOW
    # =========================================================================

    def create_transactions_for_api_reviews(
        self,
        api_reviews: List[Dict[str, Any]],
        main_product: Dict[str, Any],
        mock_users: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create transactions for original RapidAPI reviews
        Each review needs a corresponding transaction

        Args:
            api_reviews: Reviews from RapidAPI
            main_product: Main product dictionary
            mock_users: List of mock users

        Returns:
            List of transactions (one per review)
        """
        transactions = []

        for api_review in api_reviews:
            # Assign random mock user to each scraped review
            user = random.choice(mock_users)

            # Create transaction
            transaction = self._create_transaction(
                user=user,
                product=main_product,
                days_ago=random.randint(30, 730),  # 1 month to 2 years ago
                is_mock=True
            )
            transactions.append(transaction)

        return transactions

    def generate_additional_transactions(
        self,
        product: Dict[str, Any],
        users: List[Dict[str, Any]],
        existing_transactions: List[Dict[str, Any]],
        multiplier: float = 1.5
    ) -> List[Dict[str, Any]]:
        """
        Generate additional transactions beyond those with reviews
        Implements e-commerce sparsity: more transactions than reviews

        Args:
            product: Product dictionary
            users: List of users
            existing_transactions: Already created transactions
            multiplier: How many more transactions than existing (e.g., 1.5 = 50% more)

        Returns:
            List of additional transactions
        """
        # Count existing transactions for this product
        existing_count = len([t for t in existing_transactions if t['item_id'] == product['item_id']])

        # Calculate how many additional to create
        additional_count = int(existing_count * (multiplier - 1.0))

        transactions = []
        for _ in range(additional_count):
            user = random.choice(users)
            transaction = self._create_transaction(
                user=user,
                product=product,
                days_ago=random.randint(30, 730)
            )
            transactions.append(transaction)

        return transactions

    def generate_main_user_similar_transactions(
        self,
        main_user: Dict[str, Any],
        similar_products: List[Dict[str, Any]],
        count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate transactions for main user purchasing similar products
        (without reviews)

        Args:
            main_user: Main user dictionary
            similar_products: List of similar products
            count: Number of transactions to create

        Returns:
            List of transactions
        """
        transactions = []

        # Select random similar products
        selected_products = random.sample(
            similar_products,
            min(count, len(similar_products))
        )

        for product in selected_products:
            transaction = self._create_transaction(
                user=main_user,
                product=product,
                days_ago=random.randint(60, 365),  # 2-12 months ago
                is_mock=False  # Main user transaction
            )
            transactions.append(transaction)

        return transactions

    def generate_main_user_additional_transactions(
        self,
        main_user: Dict[str, Any],
        similar_products: List[Dict[str, Any]],
        existing_transactions: List[Dict[str, Any]],
        additional_count: int
    ) -> List[Dict[str, Any]]:
        """
        Generate additional main user transactions
        (purchases without reviews - more purchases than reviews)

        Args:
            main_user: Main user dictionary
            similar_products: List of similar products
            existing_transactions: Already created transactions
            additional_count: How many more transactions to create

        Returns:
            List of additional transactions
        """
        transactions = []

        # Find products main user hasn't purchased yet
        main_user_product_ids = set(
            t['item_id'] for t in existing_transactions
            if t['user_id'] == main_user['user_id']
        )

        available_products = [
            p for p in similar_products
            if p['item_id'] not in main_user_product_ids
        ]

        if not available_products:
            # If user purchased all products, allow duplicates
            available_products = similar_products

        # Select random products
        selected_products = random.sample(
            available_products,
            min(additional_count, len(available_products))
        )

        for product in selected_products:
            transaction = self._create_transaction(
                user=main_user,
                product=product,
                days_ago=random.randint(60, 365),
                is_mock=False
            )
            transactions.append(transaction)

        return transactions

    def create_main_user_exact_transaction(
        self,
        main_user: Dict[str, Any],
        main_product: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create transaction for main user purchasing exact product

        Args:
            main_user: Main user dictionary
            main_product: Main product dictionary

        Returns:
            Single transaction
        """
        return self._create_transaction(
            user=main_user,
            product=main_product,
            days_ago=random.randint(30, 180),  # 1-6 months ago
            is_mock=False
        )

    def create_transaction_for_review(
        self,
        user: Dict[str, Any],
        product: Dict[str, Any],
        days_ago: int = None
    ) -> Dict[str, Any]:
        """
        Create a single transaction that will have a review
        Helper method for review agent

        Args:
            user: User dictionary
            product: Product dictionary
            days_ago: How many days ago (optional, will randomize if not provided)

        Returns:
            Single transaction
        """
        if days_ago is None:
            days_ago = random.randint(30, 730)

        return self._create_transaction(
            user=user,
            product=product,
            days_ago=days_ago,
            is_mock=user.get('is_mock', True)
        )
