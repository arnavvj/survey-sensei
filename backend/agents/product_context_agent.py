"""
Agent 1: Product Context Generation
Generates product insights from reviews, similar products, or description.
Operates autonomously without form_data dependency.
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from config import settings
from database import db
from utils import embedding_service
import json


class ProductContext(BaseModel):
    """Product context with ordered fields for survey personalization"""
    key_features: List[str] = Field(default_factory=list, description="Standout product features")
    major_concerns: List[str] = Field(default_factory=list, description="Common user concerns")
    pros: List[str] = Field(default_factory=list, description="Positive aspects from reviews")
    cons: List[str] = Field(default_factory=list, description="Negative aspects from reviews")
    common_use_cases: List[str] = Field(default_factory=list, description="How users use this product")
    context_type: str = Field(default="generic", description="Source of context data")
    confidence_score: float = Field(default=0.5, description="Confidence level (0.0-1.0)")

    @validator('confidence_score')
    def score_must_be_valid(cls, v):
        """Ensure confidence score is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return round(v, 2)

    @validator('context_type')
    def type_must_be_valid(cls, v):
        """Ensure context_type is one of the allowed values"""
        allowed_types = ['direct_reviews', 'similar_products', 'generic']
        if v not in allowed_types:
            raise ValueError(f'context_type must be one of {allowed_types}')
        return v


class ProductContextAgent:
    """
    Agent 1: Generates product context for personalized survey questions

    Autonomous decision flow:
    1. Check if main product has reviews → Use direct reviews
    2. Check if similar products have reviews → Use similar product reviews
    3. Fallback → Use product description only
    """

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.parser = PydanticOutputParser(pydantic_object=ProductContext)

    def generate_context(self, item_id: str) -> ProductContext:
        """
        Main entry point: Generate product context autonomously

        Args:
            item_id: Product ASIN (e.g., "B09YW8BZDP")

        Returns:
            ProductContext with insights for survey generation

        Raises:
            ValueError: If product not found
        """
        # Fetch product from database
        product = db.get_product_by_id(item_id)
        if not product:
            raise ValueError(f"Product not found with ID: {item_id}")

        # Check if product has reviews (from review_count column)
        has_reviews = product.get("review_count", 0) > 0

        if has_reviews:
            # PATH 1: Main product has reviews
            return self._generate_from_main_product_reviews_and_description(product)
        else:
            # Check for similar products with reviews
            similar_products_with_reviews = self._find_similar_products_with_reviews(product)

            if similar_products_with_reviews:
                # PATH 2: Similar products have reviews
                return self._generate_from_similar_product_reviews_and_main_product_description(product, similar_products_with_reviews)
            else:
                # PATH 3: No reviews available anywhere
                return self._generate_from_main_product_description_only(product)

    def _find_similar_products_with_reviews(self, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find similar products that have reviews

        Args:
            product: Main product dictionary

        Returns:
            List of similar products with review_count > 0
        """
        # Get or generate product embedding
        product_embedding = self._get_or_generate_embedding(product)

        # Find similar products using vector search
        similar_products = db.find_similar_products(
            product_embedding=product_embedding,
            limit=settings.max_similar_products,
            threshold=settings.similarity_threshold
        )

        # Filter to only products with reviews
        products_with_reviews = [
            p for p in similar_products
            if p.get("review_count", 0) > 0 and p.get("item_id") != product.get("item_id")
        ]

        # Fetch actual reviews for these products
        for similar_product in products_with_reviews:
            reviews = db.get_product_reviews(similar_product["item_id"], limit=10)
            similar_product["reviews"] = reviews

        return products_with_reviews

    def _get_or_generate_embedding(self, product: Dict[str, Any]) -> List[float]:
        """
        Get existing embedding or generate new one

        Args:
            product: Product dictionary

        Returns:
            1536-dimensional embedding vector
        """
        product_embedding = product.get("embeddings")

        if product_embedding:
            # Handle JSON-encoded embeddings from database
            if isinstance(product_embedding, str):
                product_embedding = json.loads(product_embedding)
            return product_embedding
        else:
            # Generate embedding on-the-fly
            product_text = f"{product.get('title', '')} {product.get('description', '')}"
            return embedding_service.generate_embedding(product_text)

    # ============================================================================
    # PATH 1: Main Product Has Reviews
    # ============================================================================

    def _generate_from_main_product_reviews_and_description(self, product: Dict[str, Any]) -> ProductContext:
        """
        Generate context from main product's reviews AND main product's description/stats

        Data sources:
        - Main product's reviews (latest and top-rated)
        - Main product's description
        - Main product's stats (price, star_rating, category, etc.)

        Args:
            product: Product with review_count > 0

        Returns:
            ProductContext with high confidence (0.70-0.95)
        """
        # Fetch reviews (latest and top-rated)
        reviews = db.get_product_reviews(product["item_id"], limit=50)

        if not reviews:
            # Fallback if reviews were deleted between check and fetch
            return self._generate_from_main_product_description_only(product)

        # Rank reviews by quality, recency, and diversity
        ranked_reviews = self._rank_reviews_by_quality_and_recency(reviews)

        # Build review summary (top 30 reviews for LLM)
        review_texts = [
            f"Rating: {r['review_stars']}/5 | {r['review_text'][:200]}"  # Truncate long reviews
            for r in ranked_reviews[:30]
        ]
        review_summary = "\n".join(review_texts)

        # Build product stats
        product_stats = self._build_product_stats(product)

        # LLM Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product analysis expert. Analyze the product reviews and statistics to extract actionable insights.

Focus on extracting:
- Key features that users mention frequently
- Major concerns and questions users have
- Clear pros (what users love)
- Clear cons (what users complain about)
- Common use cases from reviews

Be specific, actionable, and prioritize patterns over one-off mentions."""),
            ("human", """Product: {title}
Brand: {brand}
Description: {description}
{product_stats}

Customer Reviews ({review_count} total):
{reviews}

Analyze this product thoroughly. Extract the most important insights for generating a personalized survey.

{format_instructions}"""),
        ])

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke({
            "title": product.get("title", "Unknown"),
            "brand": product.get("brand", "Unknown"),
            "description": product.get("description", "No description available"),
            "product_stats": product_stats,
            "review_count": len(reviews),
            "reviews": review_summary,
            "format_instructions": self.parser.get_format_instructions(),
        })

        # Parse and validate response
        context = self._parse_llm_response(
            response=response,
            fallback_type="direct_reviews",
            fallback_confidence=0.3
        )

        # Set metadata
        context.context_type = "direct_reviews"
        context.confidence_score = self._calculate_confidence_direct(len(reviews))

        return context

    # ============================================================================
    # PATH 2: Similar Products Have Reviews
    # ============================================================================

    def _generate_from_similar_product_reviews_and_main_product_description(
        self,
        product: Dict[str, Any],
        similar_products: List[Dict[str, Any]]
    ) -> ProductContext:
        """
        Generate context from similar products' reviews AND main product's description/stats

        Data sources:
        - Similar products' reviews (from vector similarity search)
        - Main product's description
        - Main product's stats (price, star_rating, category, etc.)

        Args:
            product: Main product (no reviews)
            similar_products: List of similar products with reviews

        Returns:
            ProductContext with medium confidence (0.55-0.80)
        """
        # Collect reviews from all similar products with similarity scores
        all_reviews = []
        for sim_product in similar_products:
            reviews = sim_product.get("reviews", [])
            similarity = sim_product.get("similarity", 0)

            for review in reviews:
                all_reviews.append({
                    "product": sim_product["title"],
                    "similarity": similarity,
                    "rating": review["review_stars"],
                    "text": review["review_text"],
                    "created_at": review.get("created_at"),
                    "review_stars": review["review_stars"]
                })

        # Rank reviews by similarity score, recency, and quality
        ranked_reviews = self._rank_similar_product_reviews_by_similarity_and_recency(all_reviews)

        # Build review summary (top 40 reviews for LLM)
        review_texts = [
            f"[{r['product']}] (similarity: {r['similarity']:.2f}) Rating: {r['rating']}/5 | {r['text'][:200]}"
            for r in ranked_reviews[:40]
        ]
        review_summary = "\n".join(review_texts)

        # Build product stats
        product_stats = self._build_product_stats(product)

        # Build similar products list
        similar_product_list = "\n".join([
            f"- {p['title']} (similarity: {p.get('similarity', 0):.2f}, {len(p.get('reviews', []))} reviews)"
            for p in similar_products
        ])

        # LLM Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product analysis expert analyzing a NEW product with no reviews yet.

Use reviews from similar products to INFER likely patterns for the target product.
Focus on category-level trends and features common to this product type.

Important: The target product is NEW, so infer based on similar products in its category."""),
            ("human", """Target Product (NEW - No Reviews Yet):
Title: {title}
Brand: {brand}
Description: {description}
{product_stats}

Similar Products in Same Category:
{similar_products}

Reviews from Similar Products:
{reviews}

Based on the TARGET product's description AND reviews from similar products, infer the likely key features, concerns, pros/cons, and use cases for the TARGET product.
Remember: The target product is new, so base your analysis on its description combined with category trends from similar products.

{format_instructions}"""),
        ])

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke({
            "title": product.get("title", "Unknown"),
            "brand": product.get("brand", "Unknown"),
            "description": product.get("description", "No description available"),
            "product_stats": product_stats,
            "similar_products": similar_product_list,
            "reviews": review_summary,
            "format_instructions": self.parser.get_format_instructions(),
        })

        # Parse and validate response
        context = self._parse_llm_response(
            response=response,
            fallback_type="similar_products",
            fallback_confidence=0.3
        )

        # Set metadata
        context.context_type = "similar_products"
        context.confidence_score = self._calculate_confidence_similar(
            num_similar=len(similar_products),
            num_reviews=len(all_reviews)
        )

        return context

    # ============================================================================
    # PATH 3: No Reviews Available (Description Only)
    # ============================================================================

    def _generate_from_main_product_description_only(self, product: Dict[str, Any]) -> ProductContext:
        """
        Generate context ONLY from main product's description and stats

        Data sources:
        - Main product's description
        - Main product's stats (price, star_rating, category, etc.)
        - NO reviews available (main product or similar products)

        Args:
            product: Product with no reviews (and no similar products with reviews)

        Returns:
            ProductContext with low confidence (0.40-0.50)
        """
        # Build product stats
        product_stats = self._build_product_stats(product)

        # LLM Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product analysis expert analyzing a product with NO REVIEWS available.

Use ONLY the product description and statistics to generate plausible insights.
Be realistic and acknowledge uncertainty - focus on likely concerns and features for this product category.

Important: This is speculative analysis based on description only."""),
            ("human", """Product (NO REVIEWS AVAILABLE):
Title: {title}
Brand: {brand}
Description: {description}
{product_stats}

Based ONLY on the description and stats, generate plausible:
- Key features users would care about
- Likely concerns for this product type
- Probable pros based on description
- Probable cons or limitations
- Common use cases for this product category

{format_instructions}"""),
        ])

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke({
            "title": product.get("title", "Unknown"),
            "brand": product.get("brand", "Unknown"),
            "description": product.get("description", "No description available"),
            "product_stats": product_stats,
            "format_instructions": self.parser.get_format_instructions(),
        })

        # Parse and validate response
        context = self._parse_llm_response(
            response=response,
            fallback_type="generic",
            fallback_confidence=0.3
        )

        # Set metadata
        context.context_type = "generic"
        context.confidence_score = self._calculate_confidence_generic(product)

        return context

    # ============================================================================
    # REVIEW RANKING METHODS
    # ============================================================================

    def _rank_reviews_by_quality_and_recency(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank reviews by quality (length, informativeness) and recency

        Scoring formula:
        - Recency score: Newer reviews get higher scores (exponential decay)
        - Quality score: Based on review text length (longer = more informative)
        - Star diversity: Ensure mix of ratings (not all 5-star or all 1-star)

        Args:
            reviews: List of review dictionaries

        Returns:
            Sorted list of reviews (best first)
        """
        from datetime import datetime, timezone
        import math

        if not reviews:
            return []

        # Calculate scores for each review
        scored_reviews = []
        now = datetime.now(timezone.utc)

        for review in reviews:
            # Recency score (0.0 - 1.0)
            # More recent reviews get higher scores
            created_at = review.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    # Parse timestamp string
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = now  # Fallback to now if parse fails

                # Days since review
                days_old = (now - created_at).days
                # Exponential decay: recent reviews score higher
                # 0 days = 1.0, 30 days = 0.5, 365 days = ~0.05
                recency_score = math.exp(-days_old / 180)  # Half-life of ~180 days
            else:
                recency_score = 0.5  # Neutral score if timestamp missing

            # Quality score (0.0 - 1.0)
            # Based on review text length (longer reviews tend to be more informative)
            review_text = review.get("review_text", "")
            text_length = len(review_text)
            # Normalize: 0-100 chars = 0.3, 100-300 = 0.7, 300+ = 1.0
            if text_length < 100:
                quality_score = 0.3 + (text_length / 100) * 0.4
            elif text_length < 300:
                quality_score = 0.7 + ((text_length - 100) / 200) * 0.3
            else:
                quality_score = 1.0

            # Star diversity bonus (ensure we get mix of ratings)
            # Middle ratings (3-4 stars) get slight boost for diversity
            stars = review.get("review_stars", 3)
            if stars == 3 or stars == 4:
                diversity_bonus = 0.1
            else:
                diversity_bonus = 0.0

            # Combined score (weighted)
            final_score = (
                recency_score * 0.50 +      # 50% weight on recency
                quality_score * 0.40 +      # 40% weight on quality
                diversity_bonus * 0.10      # 10% weight on diversity
            )

            scored_reviews.append({
                **review,
                "ranking_score": final_score
            })

        # Sort by score (highest first)
        scored_reviews.sort(key=lambda x: x["ranking_score"], reverse=True)

        return scored_reviews

    def _rank_similar_product_reviews_by_similarity_and_recency(
        self,
        reviews: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank similar product reviews by similarity score, recency, and quality

        Scoring formula:
        - Similarity score: Higher similarity products get priority
        - Recency score: Newer reviews more relevant
        - Quality score: Longer, more informative reviews
        - Star diversity: Mix of ratings

        Args:
            reviews: List of review dictionaries with 'similarity' field

        Returns:
            Sorted list of reviews (best first)
        """
        from datetime import datetime, timezone
        import math

        if not reviews:
            return []

        scored_reviews = []
        now = datetime.now(timezone.utc)

        for review in reviews:
            # Similarity score (0.0 - 1.0) - already provided
            similarity_score = review.get("similarity", 0.5)

            # Recency score (0.0 - 1.0)
            created_at = review.get("created_at")
            if created_at:
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    except:
                        created_at = now

                days_old = (now - created_at).days
                recency_score = math.exp(-days_old / 180)  # Half-life of ~180 days
            else:
                recency_score = 0.5

            # Quality score (0.0 - 1.0)
            review_text = review.get("text", "")
            text_length = len(review_text)
            if text_length < 100:
                quality_score = 0.3 + (text_length / 100) * 0.4
            elif text_length < 300:
                quality_score = 0.7 + ((text_length - 100) / 200) * 0.3
            else:
                quality_score = 1.0

            # Star diversity bonus
            stars = review.get("review_stars", 3)
            if stars == 3 or stars == 4:
                diversity_bonus = 0.1
            else:
                diversity_bonus = 0.0

            # Combined score (weighted - similarity gets highest weight for Path 2)
            final_score = (
                similarity_score * 0.40 +   # 40% weight on similarity (HIGHEST)
                recency_score * 0.35 +      # 35% weight on recency
                quality_score * 0.20 +      # 20% weight on quality
                diversity_bonus * 0.05      # 5% weight on diversity
            )

            scored_reviews.append({
                **review,
                "ranking_score": final_score
            })

        # Sort by score (highest first)
        scored_reviews.sort(key=lambda x: x["ranking_score"], reverse=True)

        return scored_reviews

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _build_product_stats(self, product: Dict[str, Any]) -> str:
        """Build formatted product statistics for LLM prompt"""
        stats_parts = []

        if product.get("price"):
            stats_parts.append(f"Price: ${product['price']:.2f}")

        if product.get("star_rating"):
            stats_parts.append(f"Average Rating: {product['star_rating']:.1f}/5.0")

        if product.get("num_ratings"):
            stats_parts.append(f"Total Ratings: {product['num_ratings']:,}")

        if product.get("category"):
            stats_parts.append(f"Category: {product['category']}")

        return "\n".join(stats_parts) if stats_parts else "No additional statistics available"

    def _parse_llm_response(
        self,
        response: Any,
        fallback_type: str,
        fallback_confidence: float
    ) -> ProductContext:
        """
        Parse LLM response with robust error handling

        Args:
            response: LangChain response object
            fallback_type: Context type for fallback
            fallback_confidence: Confidence score for fallback

        Returns:
            ProductContext (either parsed or fallback)
        """
        try:
            # Extract text from response
            response_text = response.content if hasattr(response, "content") else str(response)

            # Strip markdown code blocks if present
            if response_text.strip().startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            # Parse JSON
            json_obj = json.loads(response_text)

            # Remove extra fields not in schema
            allowed_fields = {
                'key_features', 'major_concerns', 'pros', 'cons',
                'common_use_cases', 'context_type', 'confidence_score'
            }
            json_obj = {k: v for k, v in json_obj.items() if k in allowed_fields}

            # Create ProductContext
            context = ProductContext(**json_obj)
            return context

        except Exception as e:
            # Log error for debugging
            print(f"[ProductContextAgent] Error parsing LLM response: {e}")
            print(f"[ProductContextAgent] Response text preview: {str(response)[:500]}")

            # Return fallback context
            return ProductContext(
                key_features=["Unable to analyze - please check logs"],
                major_concerns=["Unable to analyze - please check logs"],
                pros=["Unable to analyze - please check logs"],
                cons=["Unable to analyze - please check logs"],
                common_use_cases=["General use"],
                context_type=fallback_type,
                confidence_score=fallback_confidence
            )

    def _calculate_confidence_direct(self, num_reviews: int) -> float:
        """
        Calculate confidence score for direct reviews path

        Formula: 0.70 + (num_reviews / 100) capped at 0.95

        Examples:
        - 10 reviews → 0.80
        - 25 reviews → 0.95 (capped)
        - 50 reviews → 0.95 (capped)

        Args:
            num_reviews: Number of reviews analyzed

        Returns:
            Confidence score (0.70-0.95)
        """
        base_confidence = 0.70
        bonus = min(0.25, num_reviews / 100)  # Max bonus of 0.25
        return min(0.95, base_confidence + bonus)

    def _calculate_confidence_similar(self, num_similar: int, num_reviews: int) -> float:
        """
        Calculate confidence score for similar products path

        Formula: 0.55 + (num_similar / 10) + (num_reviews / 150) capped at 0.80

        Examples:
        - 3 similar, 20 reviews → 0.55 + 0.30 + 0.13 = 0.78
        - 5 similar, 40 reviews → 0.55 + 0.25 = 0.80 (capped)

        Args:
            num_similar: Number of similar products found
            num_reviews: Total reviews from similar products

        Returns:
            Confidence score (0.55-0.80)
        """
        base_confidence = 0.55
        similar_bonus = min(0.15, num_similar / 20)  # Max 0.15 bonus
        review_bonus = min(0.10, num_reviews / 150)  # Max 0.10 bonus
        return min(0.80, base_confidence + similar_bonus + review_bonus)

    def _calculate_confidence_generic(self, product: Dict[str, Any]) -> float:
        """
        Calculate confidence score for description-only path

        Formula: 0.40 + bonuses for available data
        - Has description: +0.05
        - Has price: +0.02
        - Has star_rating: +0.03

        Max: 0.50

        Args:
            product: Product dictionary

        Returns:
            Confidence score (0.40-0.50)
        """
        base_confidence = 0.40
        bonus = 0.0

        if product.get("description") and len(product["description"]) > 50:
            bonus += 0.05
        if product.get("price"):
            bonus += 0.02
        if product.get("star_rating"):
            bonus += 0.03

        return min(0.50, base_confidence + bonus)


# Global agent instance
product_context_agent = ProductContextAgent()
