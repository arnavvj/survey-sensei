"""
MOCK_DATA_ORCHESTRATOR
Coordinates all MOCK_DATA_MINI_AGENTS to generate complete simulation environment
Enhanced with parallel processing for faster generation
"""

from typing import Dict, Any, List
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .mock_pdt_agent import MockProductAgent
from .mock_usr_agent import MockUserAgent
from .mock_trx_agent import MockTransactionAgent
from .mock_rvw_agent import MockReviewAgent
from .cache import get_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataOrchestrator:
    """
    Orchestrates mock data generation for all 12 simulation scenarios
    Cost-optimized workflow using gpt-4o-mini
    Enhanced with parallel processing for faster generation
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
        Generate complete mock data environment based on scenario

        Args:
            form_data: User form submission with:
                - userName, userEmail, userAge, userLocation, userZip, userGender
                - productPurchased: 'exact' or 'similar'
                - userPurchasedExact: 'YES' or 'NO'
                - userPurchasedSimilar: 'YES' or 'NO'
                - userReviewedExact: 'YES' or 'NO'
                - userReviewedSimilar: 'YES' or 'NO'
            main_product: Product from RapidAPI
            api_reviews: Reviews from RapidAPI (if available)
            scenario_config: Scenario-specific configuration

        Returns:
            Dictionary with all generated data:
                - products: List[Dict]
                - users: List[Dict]
                - transactions: List[Dict]
                - reviews: List[Dict]
        """
        logger.info("🚀 Starting MOCK_DATA_MINI_AGENT pipeline")

        # PHASE 1 & 2: Generate Products and Users in Parallel (no dependencies)
        logger.info("⚡ Running Product and User generation in parallel")

        async def generate_products():
            logger.info("📦 MOCK_PDT_MINI_AGENT: Generating similar products")
            similar_products = self.pdt_agent.generate_similar_products(
                main_product=main_product,
                count=scenario_config.get('similar_product_count', 5),
                use_cache=self.use_cache,
                generate_embeddings=scenario_config.get('generate_embeddings', False)
            )
            logger.info(f"✅ Generated {len(similar_products)} similar products")
            return [main_product] + similar_products

        async def generate_users():
            logger.info("👥 MOCK_USR_MINI_AGENT: Generating user personas")
            main_user = self.usr_agent.generate_main_user(form_data)
            mock_users = self.usr_agent.generate_mock_users(
                main_user=main_user,
                count=scenario_config.get('mock_user_count', 15)
            )
            logger.info(f"✅ Generated main user + {len(mock_users)} mock users")
            return [main_user] + mock_users

        # Run products and users generation concurrently
        all_products, all_users = await asyncio.gather(
            generate_products(),
            generate_users()
        )

        # PHASE 3: Transactions
        logger.info("💳 MOCK_TRX_MINI_AGENT: Generating transactions")
        transactions = self.trx_agent.generate_transactions(
            scenario=form_data,
            users=all_users,
            products=all_products
        )
        logger.info(f"✅ Generated {len(transactions)} transactions")

        # PHASE 4: Reviews
        logger.info("⭐ MOCK_RVW_MINI_AGENT: Generating reviews")
        reviews = []

        # Reviews from RapidAPI templates (for main product)
        if api_reviews and form_data['productPurchased'] == 'exact':
            api_based_reviews = self.rvw_agent.generate_reviews_from_api_templates(
                api_reviews=api_reviews[:scenario_config.get('api_review_count', 10)],
                transactions=[t for t in transactions if t['item_id'] == main_product['item_id']],
                product_id=main_product['item_id']
            )
            reviews.extend(api_based_reviews)
            logger.info(f"✅ Generated {len(api_based_reviews)} reviews from RapidAPI templates")

        # Agent-generated reviews (for products without templates)
        for product in all_products:
            product_transactions = [t for t in transactions if t['item_id'] == product['item_id']]
            existing_review_count = len([r for r in reviews if r['item_id'] == product['item_id']])

            # Determine how many more reviews needed
            target_reviews = scenario_config.get('reviews_per_product', 20)
            remaining = target_reviews - existing_review_count

            if remaining > 0:
                agent_reviews = self.rvw_agent.generate_agent_reviews(
                    product=product,
                    transactions=product_transactions,
                    count=remaining
                )
                reviews.extend(agent_reviews)

        logger.info(f"✅ Total reviews generated: {len(reviews)}")

        # Return complete dataset
        result = {
            'products': all_products,
            'users': all_users,
            'transactions': transactions,
            'reviews': reviews,
            'metadata': {
                'scenario': scenario_config.get('scenario_id'),
                'product_count': len(all_products),
                'user_count': len(all_users),
                'transaction_count': len(transactions),
                'review_count': len(reviews),
                'main_product_id': main_product['item_id'],
                'main_user_id': main_user['user_id'],
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

        # Estimate token usage
        similar_products = scenario_config.get('similar_product_count', 5)
        mock_users = scenario_config.get('mock_user_count', 15)
        reviews_to_generate = scenario_config.get('reviews_per_product', 20) * similar_products

        # Products: ~300 tokens input, ~800 output per batch (5 products)
        product_batches = (similar_products + 4) // 5
        product_input_tokens = product_batches * 300
        product_output_tokens = product_batches * 800

        # Users: ~250 tokens input, ~1200 output per batch (10 users)
        user_batches = (mock_users + 9) // 10
        user_input_tokens = user_batches * 250
        user_output_tokens = user_batches * 1200

        # Reviews: ~200 tokens input, ~600 output per batch (5 reviews)
        review_batches = (reviews_to_generate + 4) // 5
        review_input_tokens = review_batches * 200
        review_output_tokens = review_batches * 600

        total_input_tokens = product_input_tokens + user_input_tokens + review_input_tokens
        total_output_tokens = product_output_tokens + user_output_tokens + review_output_tokens

        total_cost = (
            (total_input_tokens / 1000) * input_cost_per_1k +
            (total_output_tokens / 1000) * output_cost_per_1k
        )

        return {
            'total_estimated_cost_usd': round(total_cost, 4),
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'breakdown': {
                'products': round((product_input_tokens / 1000) * input_cost_per_1k + (product_output_tokens / 1000) * output_cost_per_1k, 4),
                'users': round((user_input_tokens / 1000) * input_cost_per_1k + (user_output_tokens / 1000) * output_cost_per_1k, 4),
                'reviews': round((review_input_tokens / 1000) * input_cost_per_1k + (review_output_tokens / 1000) * output_cost_per_1k, 4),
            }
        }
