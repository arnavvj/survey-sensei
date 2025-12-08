"""
MOCK_PDT_MINI_AGENT - Product Mock Data Generator
Generates similar products based on main product from RapidAPI
Uses gpt-4o-mini for cost-effective generation
Enhanced with category support and embeddings
"""

from typing import List, Dict, Any, Optional
import random
from .base import BaseMockAgent
from .cache import get_cache


# Minimal product category mappings for common e-commerce categories
PRODUCT_CATEGORIES = {
    'electronics': ['laptop', 'phone', 'tablet', 'camera', 'headphone', 'speaker', 'mouse', 'keyboard'],
    'clothing': ['shirt', 'pants', 'dress', 'shoes', 'jacket', 'sweater', 'jeans'],
    'home': ['furniture', 'decor', 'kitchen', 'bedding', 'lighting', 'storage'],
    'sports': ['equipment', 'apparel', 'fitness', 'outdoor', 'cycling'],
    'beauty': ['skincare', 'makeup', 'haircare', 'fragrance', 'tools'],
    'books': ['fiction', 'non-fiction', 'textbook', 'children'],
    'toys': ['action figure', 'puzzle', 'board game', 'doll', 'educational'],
}


class MockProductAgent(BaseMockAgent):
    """
    Generates mock similar products for Product/Customer Context Agents
    Creates realistic product variations while maintaining semantic similarity
    Enhanced with category detection and embeddings generation
    """

    def __init__(self):
        super().__init__()
        self.cache = get_cache()

    def detect_category(self, product_title: str) -> Optional[str]:
        """
        Detect product category from title

        Args:
            product_title: Product title

        Returns:
            Detected category or None
        """
        title_lower = product_title.lower()
        for category, keywords in PRODUCT_CATEGORIES.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        return 'general'

    def generate_similar_products(
        self,
        main_product: Dict[str, Any],
        count: int = 5,
        use_cache: bool = True,
        generate_embeddings: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate similar mock products based on main product

        Args:
            main_product: Main product from RapidAPI with fields:
                - item_id (ASIN)
                - title
                - brand
                - description
                - price
                - star_rating
                - num_ratings
            count: Number of similar products to generate
            use_cache: Whether to use cached data
            generate_embeddings: Whether to generate vector embeddings

        Returns:
            List of mock product dictionaries
        """
        # Check cache first
        if use_cache:
            cache_key = {
                'agent': 'mock_pdt',
                'main_product_id': main_product['item_id'],
                'count': count
            }
            cached_data = self.cache.get(**cache_key)
            if cached_data:
                return cached_data
        system_prompt = """You are a product data engineer creating realistic similar products for an e-commerce demo.
Generate products that are semantically similar but distinct from the main product.
Products should vary in:
- Specific features (size, color, model, version)
- Price (±20-40% of main product)
- Ratings (realistic variation based on quality indicators)
- Brand (include both same brand and competitor brands)

Keep titles concise and realistic. Return ONLY valid JSON."""

        user_prompt = f"""Generate {count} similar products to this main product:

Title: {main_product['title']}
Brand: {main_product.get('brand', 'Unknown')}
Price: ${main_product.get('price', 0):.2f}
Rating: {main_product.get('star_rating', 0)} stars

Return JSON array with these fields for each product:
[
  {{
    "item_id": "unique 10-char alphanumeric ASIN like B08XYZ1234",
    "title": "product title (similar but distinct)",
    "brand": "brand name (same or competitor)",
    "description": "brief 1-2 sentence description",
    "price": price as number,
    "star_rating": rating 1.0-5.0 as number,
    "num_ratings": count as number (50-5000 range)
  }}
]

Generate diverse, realistic variations."""

        response = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000,  # Slightly higher for multiple products
            temperature=0.9  # High diversity for mock data
        )

        products = self._parse_json_response(response)

        # Ensure products is a list
        if isinstance(products, dict):
            products = [products]

        # Detect category for main product
        category = self.detect_category(main_product['title'])

        # Add mock data tracking fields and category
        for product in products:
            product['is_mock'] = True
            product['product_url'] = f"https://amazon.com/dp/{product['item_id']}"
            product['photos'] = self._generate_placeholder_photos()
            product['category'] = category

            # Generate embeddings if requested
            if generate_embeddings:
                embedding_text = f"{product['title']} {product.get('description', '')}"
                product['embeddings'] = self.generate_single_embedding(embedding_text)
            else:
                product['embeddings'] = None

        products = products[:count]

        # Cache the results
        if use_cache:
            cache_key = {
                'agent': 'mock_pdt',
                'main_product_id': main_product['item_id'],
                'count': count
            }
            self.cache.set(products, **cache_key)

        return products

    def _generate_placeholder_photos(self) -> List[str]:
        """Generate placeholder photo URLs"""
        # Use a placeholder image service for demo
        count = random.randint(2, 5)
        return [
            f"https://via.placeholder.com/500x500?text=Product+Image+{i+1}"
            for i in range(count)
        ]

    def _generate_asin(self) -> str:
        """Generate realistic-looking ASIN"""
        import string
        chars = string.ascii_uppercase + string.digits
        return 'B' + ''.join(random.choices(chars, k=9))
