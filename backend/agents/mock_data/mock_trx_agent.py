"""
MOCK_TRX_MINI_AGENT - Transaction Mock Data Generator
Generates realistic purchase transactions for simulation scenarios
Uses simple rules-based logic (no LLM) to minimize costs
"""

from typing import List, Dict, Any
import random
import uuid
from datetime import datetime, timedelta


class MockTransactionAgent:
    """
    Generates mock transactions using deterministic rules
    No LLM calls needed - saves costs while maintaining realism
    """

    def generate_transactions(
        self,
        scenario: Dict[str, Any],
        users: List[Dict[str, Any]],
        products: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate mock transactions based on simulation scenario

        Args:
            scenario: Scenario configuration with fields:
                - productPurchased: 'exact' or 'similar'
                - userPurchasedExact: 'YES' or 'NO'
                - userPurchasedSimilar: 'YES' or 'NO'
                - userReviewedExact: 'YES' or 'NO'
                - userReviewedSimilar: 'YES' or 'NO'
            users: List of user dictionaries (main + mock users)
            products: List of product dictionaries (main + mock products)

        Returns:
            List of transaction dictionaries
        """
        transactions = []

        # Find main user and main product
        main_user = next(u for u in users if u.get('is_main_user'))
        main_product = next(p for p in products if not p.get('is_mock'))

        # Generate main user transaction if needed
        if scenario['userPurchasedExact'] == 'YES':
            trx = self._create_transaction(
                user=main_user,
                product=main_product,
                days_ago=random.randint(30, 180)  # 1-6 months ago
            )
            transactions.append(trx)

        # Generate main user similar product transactions if needed
        if scenario['userPurchasedSimilar'] == 'YES':
            similar_products = [p for p in products if p.get('is_mock')]
            count = random.randint(1, 3)  # 1-3 similar product purchases
            for product in random.sample(similar_products, min(count, len(similar_products))):
                trx = self._create_transaction(
                    user=main_user,
                    product=product,
                    days_ago=random.randint(60, 365)  # 2-12 months ago
                )
                transactions.append(trx)

        # Generate mock user transactions for ecosystem
        mock_users = [u for u in users if not u.get('is_main_user')]

        # Ensure product has reviews (from mock users) if needed
        if scenario['productPurchased'] == 'exact':
            # Product cold/warm - generate transactions for main product
            review_count = random.randint(10, 50) if scenario.get('has_reviews') else 0
            for i in range(review_count):
                user = random.choice(mock_users)
                trx = self._create_transaction(
                    user=user,
                    product=main_product,
                    days_ago=random.randint(30, 730)  # 1 month to 2 years
                )
                transactions.append(trx)

        # Generate transactions for similar products (ecosystem)
        similar_products = [p for p in products if p.get('is_mock')]
        for product in similar_products:
            trx_count = random.randint(5, 20)  # Each similar product has 5-20 transactions
            for i in range(trx_count):
                user = random.choice(mock_users)
                trx = self._create_transaction(
                    user=user,
                    product=product,
                    days_ago=random.randint(30, 730)
                )
                transactions.append(trx)

        return transactions

    def _create_transaction(
        self,
        user: Dict[str, Any],
        product: Dict[str, Any],
        days_ago: int
    ) -> Dict[str, Any]:
        """Create a single transaction"""
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
            'is_mock': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        return transaction
