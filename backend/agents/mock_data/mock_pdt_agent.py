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
        # Detect category from main product
        category = self.detect_category(main_product['title'])
        main_brand = main_product.get('brand', 'Unknown')

        # If main brand is Unknown, try to extract from title
        if main_brand == 'Unknown':
            # Simple extraction: first word before common product keywords
            title_words = main_product['title'].split()
            if len(title_words) > 0:
                main_brand = title_words[0]

        system_prompt = """You are a product data engineer creating realistic similar products for an e-commerce demo.
Generate products that are semantically similar but distinct from the main product.
Products should vary in:
- Specific features (size, color, model, version)
- Price (±20-40% of main product)
- Ratings (realistic variation based on quality indicators)
- Brand (mix of same brand and 2-3 competitor brands)

IMPORTANT:
- ALL products MUST be in the SAME CATEGORY as the main product
- Include the EXACT brand name for at least 40% of similar products
- Keep titles concise and realistic
- Return ONLY valid JSON."""

        user_prompt = f"""Generate {count} similar products to this main product:

Title: {main_product['title']}
Brand: {main_brand}
Category: {category}
Price: ${main_product.get('price', 0):.2f}
Rating: {main_product.get('star_rating', 0)} stars

Return JSON array with these fields for each product:
[
  {{
    "item_id": "unique 10-char alphanumeric ASIN like B08XYZ1234",
    "title": "product title (similar but distinct, SAME category)",
    "brand": "brand name (use '{main_brand}' for ~40% of products, competitors for rest)",
    "description": "brief 1-2 sentence description",
    "price": price as number,
    "star_rating": rating 1.0-5.0 as number,
    "num_ratings": count as number (50-5000 range)
  }}
]

CRITICAL: All products MUST be {category} products similar to the main product.
Generate diverse, realistic variations of the SAME product type."""

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

        # Add mock data tracking fields and category
        for product in products:
            product['is_mock'] = True
            product['product_url'] = f"https://amazon.com/dp/{product['item_id']}"
            product['photos'] = self._generate_placeholder_photos()
            product['category'] = category  # Use category detected earlier

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

    def generate_diverse_products(
        self,
        count: int = 3,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate completely different products for organic ecosystem diversity
        These products are from various categories to simulate a real marketplace

        Args:
            count: Number of diverse products to generate
            use_cache: Whether to use cached data

        Returns:
            List of diverse product dictionaries
        """
        import hashlib
        import time

        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(
                endpoint="diverse-products",
                count=count,
                timestamp=int(time.time() / 3600)  # Cache for 1 hour
            )
            cached_data = self._get_cached_data(cache_key) if hasattr(self, '_get_cached_data') else None
            if cached_data:
                return cached_data

        # Add timestamp-based seed for variation
        seed = hashlib.md5(f"{time.time()}{count}".encode()).hexdigest()[:8]

        system_prompt = """You are a product catalog engineer creating diverse products for an e-commerce marketplace.
Generate products from COMPLETELY DIFFERENT categories to create organic diversity.

DIVERSITY REQUIREMENTS:
- Each product MUST be from a DIFFERENT category
- Mix categories: electronics, home, sports, beauty, books, toys, fashion, kitchen, etc.
- Vary price points widely ($10-$500)
- Realistic brands for each category
- Diverse ratings (3.5-5.0 stars)

Return ONLY valid JSON."""

        user_prompt = f"""Generate {count} COMPLETELY DIFFERENT products from various categories.

Uniqueness seed: {seed}

Return JSON array with these fields for each product:
[
  {{
    "item_id": "unique 10-char alphanumeric ASIN like B08XYZ1234",
    "title": "product title (specific and realistic)",
    "brand": "appropriate brand for this product category",
    "category": "specific category (electronics, home, sports, beauty, etc.)",
    "description": "brief 1-2 sentence description",
    "price": price as number (vary widely: $10-$500),
    "star_rating": rating 3.5-5.0 as number,
    "num_ratings": count as number (100-3000 range)
  }}
]

CRITICAL: Each product must be from a COMPLETELY DIFFERENT category. Create organic marketplace diversity."""

        response = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1000,
            temperature=1.0  # Maximum creativity for diversity
        )

        products = self._parse_json_response(response)

        # Ensure products is a list
        if isinstance(products, dict):
            products = [products]

        # Add mock data tracking fields
        for product in products:
            product['is_mock'] = True
            product['product_url'] = f"https://amazon.com/dp/{product['item_id']}"
            product['photos'] = self._generate_placeholder_photos()
            # category already set by LLM
            product['embeddings'] = None

        products = products[:count]

        # Cache the results
        if use_cache and hasattr(self, '_save_to_cache'):
            cache_key = self._get_cache_key(
                endpoint="diverse-products",
                count=count,
                timestamp=int(time.time() / 3600)
            )
            self._save_to_cache(cache_key, products)

        return products

    def _get_cache_key(self, **params) -> str:
        """Generate cache key from parameters"""
        import json
        import hashlib
        sorted_params = json.dumps(params, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()

    def _get_cached_data(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached data if available"""
        return self.cache.get(cache_key=cache_key) if hasattr(self.cache, 'get') else None

    def _save_to_cache(self, cache_key: str, data: List[Dict[str, Any]]) -> None:
        """Save data to cache"""
        if hasattr(self.cache, 'set'):
            self.cache.set(data, cache_key=cache_key)

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
