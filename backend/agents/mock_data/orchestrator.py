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

        # 1.a: Initialize product_df with main product (defer embeddings to batch generation)
        enable_embeddings = scenario_config.get('generate_embeddings', True)  # Default: True
        main_product['embeddings'] = None  # Will be generated in batch later

        all_products = [main_product]

        # 1.b: Generate and append mock similar products (defer embeddings)
        similar_products = self.pdt_agent.generate_similar_products(
            main_product=main_product,
            count=scenario_config.get('similar_product_count', 5),
            use_cache=self.use_cache,
            generate_embeddings=False  # Defer to batch generation
        )
        all_products.extend(similar_products)

        # 1.c: Generate diverse/different products for organic ecosystem (defer embeddings)
        diverse_product_count = scenario_config.get('diverse_product_count', 3)
        diverse_products = self.pdt_agent.generate_diverse_products(
            count=diverse_product_count,
            use_cache=self.use_cache,
            generate_embeddings=False  # Defer to batch generation
        )
        all_products.extend(diverse_products)
        logger.info(f"✅ Products: 1 main + {len(similar_products)} similar + {len(diverse_products)} diverse = {len(all_products)} total")

        # 1.c: Initialize user_df with main user (defer embeddings)
        main_user = self.usr_agent.generate_main_user(
            form_data,
            generate_embeddings=False  # Defer to batch generation
        )
        all_users = [main_user]

        # 1.d: Calculate realistic user count based on expected reviews
        # Realistic e-commerce: users >> transactions >> reviews
        # For warm products: users = reviews * 1.5 (60-70% purchase rate among interested users)
        # For cold products: users = similar_product_reviews * 1.2
        expected_main_reviews = scenario_config.get('main_product_reviews', 100)
        expected_similar_reviews = scenario_config.get('similar_product_reviews', 20) * scenario_config.get('similar_product_count', 5)
        total_expected_reviews = expected_main_reviews + expected_similar_reviews

        # Calculate user count: Need enough users so each buys max 1-2 products
        # Users = (total reviews * 1.5) to ensure realistic sparsity
        calculated_user_count = max(int(total_expected_reviews * 1.5), scenario_config.get('mock_user_count', 15))

        # Generate and append mock users (defer embeddings)
        mock_users = self.usr_agent.generate_mock_users(
            main_user=main_user,
            count=calculated_user_count,
            generate_embeddings=False  # Defer to batch generation
        )
        all_users.extend(mock_users)
        logger.info(f"✅ Users: 1 main + {len(mock_users)} mock = {len(all_users)} total (calculated for realistic sparsity)")

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

                # Then convert API reviews to our format (defer embeddings)
                api_review_objects = self.rvw_agent.convert_api_reviews_to_db_format(
                    api_reviews=api_reviews,
                    transactions=api_transactions,
                    main_product=main_product,
                    generate_embeddings=False  # Defer to batch generation
                )
                reviews.extend(api_review_objects)
                logger.info(f"✅ Added {len(api_review_objects)} original scraped reviews")

            # 2.2: Generate additional mock reviews to meet sentimentSpread requirement (defer embeddings)
            sentiment_spread = form_data.get('sentimentSpread', {'good': 70, 'neutral': 20, 'bad': 10})
            additional_reviews, additional_transactions = self.rvw_agent.generate_reviews_for_sentiment_spread(
                main_product=main_product,
                mock_users=mock_users,
                existing_reviews=reviews,
                sentiment_spread=sentiment_spread,
                target_total=scenario_config.get('main_product_reviews', 100),
                generate_embeddings=False  # Defer to batch generation
            )
            reviews.extend(additional_reviews)
            transactions.extend(additional_transactions)
            logger.info(f"✅ Added {len(additional_reviews)} sentiment-spread reviews for main product")

            # 2.3: Generate additional transactions (purchases WITHOUT reviews)
            # Realistic: 40-60% of purchasers leave reviews, so transactions = reviews / 0.5
            # But ensure no user buys same product multiple times
            target_transactions = int(len([r for r in reviews if r['item_id'] == main_product['item_id']]) / 0.6)
            current_transactions = len([t for t in transactions if t['item_id'] == main_product['item_id']])
            additional_needed = max(0, target_transactions - current_transactions)

            # Find users who haven't purchased this product yet
            users_who_purchased = set(t['user_id'] for t in transactions if t['item_id'] == main_product['item_id'])
            available_users = [u for u in mock_users if u['user_id'] not in users_who_purchased]

            # Generate transactions from new users only
            extra_count = min(additional_needed, len(available_users))
            extra_main_transactions = []
            for i in range(extra_count):
                user = available_users[i]
                transaction = self.trx_agent._create_transaction(
                    user=user,
                    product=main_product,
                    days_ago=random.randint(30, 730),
                    is_mock=True
                )
                extra_main_transactions.append(transaction)

            transactions.extend(extra_main_transactions)
            logger.info(f"✅ Added {len(extra_main_transactions)} additional transactions (purchases without reviews) for main product")

        else:
            logger.info("⏭️  STEP 2: Main product has NO reviews - skipping...")

        # ============================================================
        # STEP 3: DECISION - hasSimilarProductsReviews?
        # ============================================================
        has_similar_products_reviews = form_data.get('hasSimilarProductsReviews') == 'yes'

        if has_similar_products_reviews:
            logger.info("⭐ STEP 3: Similar products have reviews - generating...")

            # Generate reviews for mock products (random distribution, defer embeddings)
            similar_reviews, similar_transactions = self.rvw_agent.generate_reviews_for_similar_products(
                similar_products=similar_products,
                generate_embeddings=False,  # Defer to batch generation
                mock_users=mock_users,
                reviews_per_product=scenario_config.get('similar_product_reviews', 20)
            )
            reviews.extend(similar_reviews)
            transactions.extend(similar_transactions)
            logger.info(f"✅ Added {len(similar_reviews)} reviews for similar products")

            # Generate additional transactions for similar products (purchases without reviews)
            for product in similar_products:
                product_reviews = [r for r in reviews if r['item_id'] == product['item_id']]
                target_transactions = int(len(product_reviews) / 0.6) if len(product_reviews) > 0 else 0
                current_transactions = len([t for t in transactions if t['item_id'] == product['item_id']])
                additional_needed = max(0, target_transactions - current_transactions)

                # Find users who haven't purchased this product yet
                users_who_purchased = set(t['user_id'] for t in transactions if t['item_id'] == product['item_id'])
                available_users = [u for u in mock_users if u['user_id'] not in users_who_purchased]

                # Generate transactions from new users only
                extra_count = min(additional_needed, len(available_users))
                for i in range(extra_count):
                    user = available_users[i]
                    transaction = self.trx_agent._create_transaction(
                        user=user,
                        product=product,
                        days_ago=random.randint(30, 730),
                        is_mock=True
                    )
                    transactions.append(transaction)

            logger.info(f"✅ Total transactions for similar products: {len([t for t in transactions if t['item_id'] in [p['item_id'] for p in similar_products]])}")

        else:
            logger.info("⏭️  STEP 3: Similar products have NO reviews - skipping...")

        # ============================================================
        # STEP 4: DECISION - userPurchasedSimilar?
        # ============================================================
        user_purchased_similar = form_data.get('userPurchasedSimilar') == 'YES'

        if user_purchased_similar:
            logger.info("👤 STEP 4: Main user purchased similar products - processing...")

            # SUB-BRANCH A: userReviewedSimilar?
            user_reviewed_similar = form_data.get('userReviewedSimilar') == 'YES'

            if user_reviewed_similar:
                logger.info("✍️  Sub-branch A: Main user reviewed similar products")

                # Generate main user's reviews for similar products (defer embeddings)
                main_user_similar_reviews, main_user_similar_txns = self.rvw_agent.generate_main_user_similar_reviews(
                    main_user=main_user,
                    similar_products=similar_products,
                    count=random.randint(2, 4),  # 2-4 reviews
                    generate_embeddings=False  # Defer to batch generation
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
            user_purchased_exact = form_data.get('userPurchasedExact') == 'YES'

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
                user_reviewed_exact = form_data.get('userReviewedExact') == 'YES'

                if user_reviewed_exact:
                    logger.info("⭐ Main user reviewed exact product")

                    # Generate main user's review for main product (defer embeddings)
                    exact_review = self.rvw_agent.generate_main_user_exact_review(
                        main_user=main_user,
                        main_product=main_product,
                        transaction=exact_txn,
                        generate_embeddings=False  # Defer to batch generation
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
        # STEP 5: Generate minimal activity for diverse products
        # ============================================================
        if diverse_products:
            logger.info("🌈 STEP 5: Generating minimal organic activity for diverse products...")

            for diverse_product in diverse_products:
                # Generate minimal reviews (2-5 per diverse product)
                minimal_review_count = random.randint(2, 5)
                diverse_reviews, diverse_txns = self.rvw_agent._generate_reviews_with_sentiment(
                    product=diverse_product,
                    users=mock_users,
                    count=minimal_review_count,
                    sentiment=random.choice(['good', 'good', 'neutral'])  # Mostly positive or neutral
                )
                reviews.extend(diverse_reviews)
                transactions.extend(diverse_txns)

                # Generate additional transactions (purchases without reviews)
                # Minimal activity: only 1-2 additional purchases per diverse product
                product_reviews = [r for r in reviews if r['item_id'] == diverse_product['item_id']]
                additional_purchases = random.randint(1, 2)

                # Find users who haven't purchased this product yet
                users_who_purchased = set(t['user_id'] for t in transactions if t['item_id'] == diverse_product['item_id'])
                available_users = [u for u in mock_users if u['user_id'] not in users_who_purchased]

                # Generate transactions from new users only
                extra_count = min(additional_purchases, len(available_users))
                for i in range(extra_count):
                    user = available_users[i]
                    transaction = self.trx_agent._create_transaction(
                        user=user,
                        product=diverse_product,
                        days_ago=random.randint(30, 730),
                        is_mock=True
                    )
                    transactions.append(transaction)

            logger.info(f"✅ Added minimal activity for {len(diverse_products)} diverse products")

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

        # Calculate sparsity metrics
        avg_purchases_per_user_main = len(main_product_transactions) / main_product_users if main_product_users > 0 else 0
        review_rate_main = (len(main_product_reviews) / len(main_product_transactions) * 100) if len(main_product_transactions) > 0 else 0

        logger.info(f"📊 Final Stats:")
        logger.info(f"   Products: {len(all_products)} | Users: {len(all_users)}")
        logger.info(f"   Transactions: {len(transactions)} | Reviews: {len(reviews)}")
        logger.info(f"   Main Product: {len(main_product_transactions)} txns, {len(main_product_reviews)} reviews, {main_product_users} unique buyers")
        logger.info(f"   Main Product Sparsity: {avg_purchases_per_user_main:.2f} purchases/user, {review_rate_main:.1f}% review rate")
        logger.info(f"   Main User: {len(main_user_transactions)} txns, {len(main_user_reviews)} reviews, {main_user_products} different products")

        # ============================================================
        # STEP 6: BATCH GENERATE EMBEDDINGS (OPTIMIZED)
        # ============================================================
        if enable_embeddings:
            logger.info("🔮 STEP 6: Generating embeddings in batches (optimized)...")

            # Batch generate product embeddings
            if all_products:
                logger.info(f"   → Generating embeddings for {len(all_products)} products...")
                self.pdt_agent.generate_embeddings_batch(
                    items=all_products,
                    text_builder_fn=self.pdt_agent.build_product_embedding_text,
                    batch_size=100
                )

            # Batch generate user embeddings
            if all_users:
                logger.info(f"   → Generating embeddings for {len(all_users)} users...")
                self.usr_agent.generate_embeddings_batch(
                    items=all_users,
                    text_builder_fn=self.usr_agent.build_user_embedding_text,
                    batch_size=100
                )

            # Batch generate review embeddings
            if reviews:
                logger.info(f"   → Generating embeddings for {len(reviews)} reviews...")
                self.rvw_agent.generate_embeddings_batch(
                    items=reviews,
                    text_builder_fn=self.rvw_agent.build_review_embedding_text,
                    batch_size=100
                )

            logger.info(f"✅ Batch embedding generation complete!")
        else:
            logger.info("⏭️  Skipping embeddings generation (disabled in config)")

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
