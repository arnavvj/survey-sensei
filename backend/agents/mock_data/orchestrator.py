"""
MOCK_DATA_ORCHESTRATOR
Coordinates all MOCK_DATA_MINI_AGENTS to generate complete simulation environment
Following exact e-commerce data generation workflow with proper sparsity
"""

from typing import Dict, Any, List
import logging
import asyncio
import random
from .mock_pdt_agent import MockProductAgent
from .mock_usr_agent import MockUserAgent
from .mock_trx_agent import MockTransactionAgent
from .mock_rvw_agent import MockReviewAgent
from .cache import get_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataOrchestrator:
    """
    Orchestrates mock data generation following proper e-commerce data patterns
    Implements sparse but rich data generation with realistic review/transaction ratios
    """

    def __init__(self, use_cache: bool = True):
        self.pdt_agent = MockProductAgent()
        self.usr_agent = MockUserAgent()
        self.trx_agent = MockTransactionAgent()
        self.rvw_agent = MockReviewAgent()
        self.cache = get_cache()
        self.use_cache = use_cache

    async def generate_simulation_data(
        self,
        form_data: Dict[str, Any],
        main_product: Dict[str, Any],
        api_reviews: List[Dict[str, Any]],
        scenario_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate complete mock data environment following exact workflow

        Args:
            form_data: User form submission with scenario fields
            main_product: Product from RapidAPI
            api_reviews: Reviews from RapidAPI (if available)
            scenario_config: Scenario-specific configuration

        Returns:
            Dictionary with all generated data and metadata
        """
        logger.info("🚀 Starting MOCK_DATA_MINI_AGENT pipeline (redesigned workflow)")

        # ============================================================
        # STEP 1: DATA INITIALIZATION
        # ============================================================
        logger.info("📦 STEP 1: Initializing products and users")

        # 1.a: Initialize product_df with main product
        all_products = [main_product]

        # 1.b: Generate and append mock similar products
        similar_products = self.pdt_agent.generate_similar_products(
            main_product=main_product,
            count=scenario_config.get('similar_product_count', 5),
            use_cache=self.use_cache,
            generate_embeddings=scenario_config.get('generate_embeddings', False)
        )
        all_products.extend(similar_products)
        logger.info(f"✅ Products: 1 main + {len(similar_products)} similar = {len(all_products)} total")

        # 1.c: Initialize user_df with main user
        main_user = self.usr_agent.generate_main_user(form_data)
        all_users = [main_user]

        # 1.d: Generate and append mock users
        mock_users = self.usr_agent.generate_mock_users(
            main_user=main_user,
            count=scenario_config.get('mock_user_count', 15)
        )
        all_users.extend(mock_users)
        logger.info(f"✅ Users: 1 main + {len(mock_users)} mock = {len(all_users)} total")

        # Initialize empty reviews and transactions lists
        reviews = []
        transactions = []

        # ============================================================
        # STEP 2: DECISION - hasMainProductReviews?
        # ============================================================
        has_main_product_reviews = form_data.get('hasMainProductReviews') == 'yes'

        if has_main_product_reviews:
            logger.info("⭐ STEP 2: Main product has reviews - processing...")

            # 2.1: Append ORIGINAL RapidAPI scraped reviews (main product + mock users)
            if api_reviews:
                logger.info(f"📥 Appending {len(api_reviews)} original RapidAPI reviews...")

                # First, create transactions for these reviews
                api_transactions = self.trx_agent.create_transactions_for_api_reviews(
                    api_reviews=api_reviews,
                    main_product=main_product,
                    mock_users=mock_users
                )
                transactions.extend(api_transactions)

                # Then convert API reviews to our format
                api_review_objects = self.rvw_agent.convert_api_reviews_to_db_format(
                    api_reviews=api_reviews,
                    transactions=api_transactions,
                    main_product=main_product
                )
                reviews.extend(api_review_objects)
                logger.info(f"✅ Added {len(api_review_objects)} original scraped reviews")

            # 2.2: Generate additional mock reviews to meet sentimentSpread requirement
            sentiment_spread = form_data.get('sentimentSpread', {'good': 70, 'neutral': 20, 'bad': 10})
            additional_reviews, additional_transactions = self.rvw_agent.generate_reviews_for_sentiment_spread(
                main_product=main_product,
                mock_users=mock_users,
                existing_reviews=reviews,
                sentiment_spread=sentiment_spread,
                target_total=scenario_config.get('main_product_reviews', 100)
            )
            reviews.extend(additional_reviews)
            transactions.extend(additional_transactions)
            logger.info(f"✅ Added {len(additional_reviews)} sentiment-spread reviews for main product")

            # 2.3: Generate additional transactions (sparse but rich)
            extra_main_transactions = self.trx_agent.generate_additional_transactions(
                product=main_product,
                users=mock_users,
                existing_transactions=transactions,
                multiplier=1.5  # transactions = reviews * 1.5
            )
            transactions.extend(extra_main_transactions)
            logger.info(f"✅ Added {len(extra_main_transactions)} additional transactions for main product")

        else:
            logger.info("⏭️  STEP 2: Main product has NO reviews - skipping...")

        # ============================================================
        # STEP 3: DECISION - hasSimilarProductsReviews?
        # ============================================================
        has_similar_products_reviews = form_data.get('hasSimilarProductsReviews') == 'yes'

        if has_similar_products_reviews:
            logger.info("⭐ STEP 3: Similar products have reviews - generating...")

            # Generate reviews for mock products (random distribution)
            similar_reviews, similar_transactions = self.rvw_agent.generate_reviews_for_similar_products(
                similar_products=similar_products,
                mock_users=mock_users,
                reviews_per_product=scenario_config.get('similar_product_reviews', 20)
            )
            reviews.extend(similar_reviews)
            transactions.extend(similar_transactions)
            logger.info(f"✅ Added {len(similar_reviews)} reviews for similar products")

            # Generate additional transactions for similar products
            for product in similar_products:
                extra_txns = self.trx_agent.generate_additional_transactions(
                    product=product,
                    users=mock_users,
                    existing_transactions=transactions,
                    multiplier=1.8  # More transactions than reviews
                )
                transactions.extend(extra_txns)

            logger.info(f"✅ Total transactions for similar products: {len([t for t in transactions if t['item_id'] in [p['item_id'] for p in similar_products]])}")

        else:
            logger.info("⏭️  STEP 3: Similar products have NO reviews - skipping...")

        # ============================================================
        # STEP 4: DECISION - userPurchasedSimilar?
        # ============================================================
        user_purchased_similar = form_data.get('userPurchasedSimilar') == 'yes'

        if user_purchased_similar:
            logger.info("👤 STEP 4: Main user purchased similar products - processing...")

            # SUB-BRANCH A: userReviewedSimilar?
            user_reviewed_similar = form_data.get('userReviewedSimilar') == 'yes'

            if user_reviewed_similar:
                logger.info("✍️  Sub-branch A: Main user reviewed similar products")

                # Generate main user's reviews for similar products
                main_user_similar_reviews, main_user_similar_txns = self.rvw_agent.generate_main_user_similar_reviews(
                    main_user=main_user,
                    similar_products=similar_products,
                    count=random.randint(2, 4)  # 2-4 reviews
                )
                reviews.extend(main_user_similar_reviews)
                transactions.extend(main_user_similar_txns)
                logger.info(f"✅ Added {len(main_user_similar_reviews)} main user reviews for similar products")

                # Generate additional transactions (main user bought more than reviewed)
                extra_main_user_txns = self.trx_agent.generate_main_user_additional_transactions(
                    main_user=main_user,
                    similar_products=similar_products,
                    existing_transactions=transactions,
                    additional_count=random.randint(3, 6)  # More purchases than reviews
                )
                transactions.extend(extra_main_user_txns)
                logger.info(f"✅ Added {len(extra_main_user_txns)} additional main user transactions")

            else:
                logger.info("⏭️  Sub-branch A: Main user did NOT review similar products")

                # Just generate transactions (no reviews)
                main_user_purchase_txns = self.trx_agent.generate_main_user_similar_transactions(
                    main_user=main_user,
                    similar_products=similar_products,
                    count=random.randint(3, 6)
                )
                transactions.extend(main_user_purchase_txns)
                logger.info(f"✅ Added {len(main_user_purchase_txns)} main user transactions (no reviews)")

            # SUB-BRANCH B: userPurchasedExact?
            user_purchased_exact = form_data.get('userPurchasedExact') == 'yes'

            if user_purchased_exact:
                logger.info("🎯 Sub-branch B: Main user purchased exact product")

                # Always create transaction for exact product purchase
                exact_txn = self.trx_agent.create_main_user_exact_transaction(
                    main_user=main_user,
                    main_product=main_product
                )
                transactions.append(exact_txn)
                logger.info(f"✅ Added main user exact product transaction")

                # Check if user reviewed exact product
                user_reviewed_exact = form_data.get('userReviewedExact') == 'yes'

                if user_reviewed_exact:
                    logger.info("⭐ Main user reviewed exact product")

                    # Generate main user's review for main product
                    exact_review = self.rvw_agent.generate_main_user_exact_review(
                        main_user=main_user,
                        main_product=main_product,
                        transaction=exact_txn
                    )
                    reviews.append(exact_review)
                    logger.info(f"✅ Added main user review for exact product")

                else:
                    logger.info("⏭️  Main user did NOT review exact product")

            else:
                logger.info("⏭️  Sub-branch B: Main user did NOT purchase exact product")

        else:
            logger.info("⏭️  STEP 4: Main user did NOT purchase similar products - skipping all user branches")

        # ============================================================
        # FINAL: Calculate Statistics
        # ============================================================
        main_user_id = main_user['user_id']
        main_product_id = main_product['item_id']

        # Main Product Stats
        main_product_transactions = [t for t in transactions if t['item_id'] == main_product_id]
        main_product_reviews = [r for r in reviews if r['item_id'] == main_product_id]
        main_product_users = len(set(t['user_id'] for t in main_product_transactions))

        # Main User Stats
        main_user_transactions = [t for t in transactions if t['user_id'] == main_user_id]
        main_user_reviews = [r for r in reviews if r['user_id'] == main_user_id]
        main_user_products = len(set(t['item_id'] for t in main_user_transactions))

        logger.info(f"📊 Final Stats:")
        logger.info(f"   Products: {len(all_products)} | Users: {len(all_users)}")
        logger.info(f"   Transactions: {len(transactions)} | Reviews: {len(reviews)}")
        logger.info(f"   Main Product: {len(main_product_transactions)} txns, {len(main_product_reviews)} reviews")
        logger.info(f"   Main User: {len(main_user_transactions)} txns, {len(main_user_reviews)} reviews")

        result = {
            'products': all_products,
            'users': all_users,
            'transactions': transactions,
            'reviews': reviews,
            'metadata': {
                'scenario': scenario_config.get('scenario_id'),

                # Overall ecosystem stats
                'product_count': len(all_products),
                'user_count': len(all_users),
                'transaction_count': len(transactions),
                'review_count': len(reviews),

                # Main product stats
                'main_product_id': main_product_id,
                'main_product_transactions': len(main_product_transactions),
                'main_product_reviews': len(main_product_reviews),
                'main_product_users': main_product_users,

                # Main user stats
                'main_user_id': main_user_id,
                'main_user_transactions': len(main_user_transactions),
                'main_user_reviews': len(main_user_reviews),
                'main_user_products': main_user_products,
            }
        }

        logger.info("🎉 MOCK_DATA_MINI_AGENT pipeline completed successfully")
        return result

    def estimate_cost(self, scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate API costs for mock data generation

        Args:
            scenario_config: Scenario configuration

        Returns:
            Cost estimation breakdown
        """
        # gpt-4o-mini pricing (as of 2024): $0.15/1M input tokens, $0.60/1M output tokens
        input_cost_per_1k = 0.00015
        output_cost_per_1k = 0.00060

        # Estimate tokens per agent call
        product_calls = scenario_config.get('similar_product_count', 5)
        user_calls = scenario_config.get('mock_user_count', 15) // 5  # Batch of 5
        review_calls = scenario_config.get('main_product_reviews', 100) // 5  # Batch of 5

        total_calls = product_calls + user_calls + review_calls

        # Rough estimates
        avg_input_tokens = 300
        avg_output_tokens = 500

        total_input_tokens = total_calls * avg_input_tokens
        total_output_tokens = total_calls * avg_output_tokens

        input_cost = (total_input_tokens / 1000) * input_cost_per_1k
        output_cost = (total_output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost

        return {
            'total_llm_calls': total_calls,
            'estimated_input_tokens': total_input_tokens,
            'estimated_output_tokens': total_output_tokens,
            'estimated_cost_usd': round(total_cost, 4),
            'breakdown': {
                'products': product_calls,
                'users': user_calls,
                'reviews': review_calls
            }
        }
