"""
RapidAPI Client for Real-Time Amazon Data API
Fetches product details and reviews for mock data generation
"""

import logging
import time
from typing import Dict, Any, List, Optional
import requests
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RapidAPIClient:
    """
    Client for RapidAPI Real-Time Amazon Data API
    Handles product details and review fetching with retry logic
    """

    def __init__(self):
        """Initialize RapidAPI client with configuration"""
        self.base_url = "https://real-time-amazon-data.p.rapidapi.com"
        self.api_key = getattr(settings, 'rapidapi_key', None)
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def _make_request(
        self,
        endpoint: str,
        params: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Make HTTP request to RapidAPI with retry logic

        Args:
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout in seconds

        Returns:
            API response as dictionary

        Raises:
            Exception: If all retries fail
        """
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                logger.info(f"RapidAPI request to {endpoint} (attempt {attempt + 1}/{self.max_retries})")
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=timeout
                )

                if response.status_code == 200:
                    logger.info(f"RapidAPI request successful: {endpoint}")
                    return response.json()
                elif response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limit hit, retrying in {self.retry_delay * (2 ** attempt)}s")
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"RapidAPI error {response.status_code}: {response.text}")
                    response.raise_for_status()

            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise Exception("RapidAPI request timeout after all retries")

            except Exception as e:
                logger.error(f"RapidAPI request failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise

        raise Exception("RapidAPI request failed after all retries")

    def fetch_product_details(self, asin: str, country: str = "US") -> Optional[Dict[str, Any]]:
        """
        Fetch product details by ASIN

        Args:
            asin: Amazon Standard Identification Number
            country: Country code (default: US)

        Returns:
            Product details dictionary with fields:
                - item_id (ASIN)
                - title
                - brand
                - description
                - price
                - star_rating
                - num_ratings
                - product_url
                - photos
                - category
        """
        try:
            endpoint = "/product-details"
            params = {
                "asin": asin,
                "country": country
            }

            response = self._make_request(endpoint, params)

            if not response or "data" not in response:
                logger.error(f"Invalid response format for product {asin}")
                return None

            product_data = response["data"]

            # Transform to our database format
            product = {
                'item_id': product_data.get('asin', asin),
                'title': product_data.get('product_title', ''),
                'brand': product_data.get('product_brand', 'Unknown'),
                'description': product_data.get('product_description', ''),
                'price': self._parse_price(product_data.get('product_price')),
                'star_rating': float(product_data.get('product_star_rating', 0)),
                'num_ratings': int(product_data.get('product_num_ratings', 0)),
                'product_url': product_data.get('product_url', f'https://amazon.com/dp/{asin}'),
                'photos': product_data.get('product_photos', []),
                'category': product_data.get('product_category', 'general'),
                'is_mock': False,  # Real product from RapidAPI
                'embeddings': None,  # Will be generated later if needed
            }

            logger.info(f"Successfully fetched product: {product['title']}")
            return product

        except Exception as e:
            logger.error(f"Failed to fetch product details for {asin}: {str(e)}")
            return None

    def fetch_product_reviews(
        self,
        asin: str,
        country: str = "US",
        max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Fetch product reviews by ASIN

        Args:
            asin: Amazon Standard Identification Number
            country: Country code (default: US)
            max_pages: Maximum number of review pages to fetch (each page ~10 reviews)

        Returns:
            List of review dictionaries with fields:
                - review_id
                - review_title
                - review_text
                - review_stars
                - review_date
                - verified_purchase
        """
        try:
            endpoint = "/product-reviews"
            all_reviews = []

            for page in range(1, max_pages + 1):
                params = {
                    "asin": asin,
                    "country": country,
                    "page": page
                }

                response = self._make_request(endpoint, params)

                if not response or "data" not in response:
                    logger.warning(f"No reviews found for product {asin} on page {page}")
                    break

                reviews_data = response["data"].get("reviews", [])
                if not reviews_data:
                    logger.info(f"No more reviews found for {asin} after page {page - 1}")
                    break

                # Transform to our format
                for review_data in reviews_data:
                    review = {
                        'review_id': review_data.get('review_id'),
                        'review_title': review_data.get('review_title', ''),
                        'review_comment': review_data.get('review_comment', ''),
                        'review_star_rating': int(review_data.get('review_star_rating', 5)),
                        'review_date': review_data.get('review_date'),
                        'verified_purchase': review_data.get('verified_purchase', False),
                    }
                    all_reviews.append(review)

                logger.info(f"Fetched {len(reviews_data)} reviews from page {page}")

                # Rate limiting: wait between pages
                if page < max_pages:
                    time.sleep(0.5)

            logger.info(f"Successfully fetched {len(all_reviews)} total reviews for {asin}")
            return all_reviews

        except Exception as e:
            logger.error(f"Failed to fetch reviews for {asin}: {str(e)}")
            return []

    def _parse_price(self, price_str: Any) -> float:
        """
        Parse price string to float

        Args:
            price_str: Price as string (e.g., "$29.99", "29.99")

        Returns:
            Price as float
        """
        if price_str is None:
            return 0.0

        if isinstance(price_str, (int, float)):
            return float(price_str)

        try:
            # Remove currency symbols and whitespace
            price_clean = str(price_str).replace('$', '').replace(',', '').strip()
            return float(price_clean)
        except (ValueError, AttributeError):
            logger.warning(f"Failed to parse price: {price_str}")
            return 0.0


# Global client instance
_client = None


def get_rapidapi_client() -> RapidAPIClient:
    """
    Get or create global RapidAPI client instance

    Returns:
        RapidAPIClient instance
    """
    global _client
    if _client is None:
        _client = RapidAPIClient()
    return _client
