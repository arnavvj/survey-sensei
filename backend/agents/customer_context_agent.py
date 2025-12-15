"""
Agent 2: Autonomous customer context generation from user behavior and demographics.
Upgraded to work without form_data dependency with smart ranking algorithms.
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any
from config import settings
from database import db
from utils import embedding_service
from datetime import datetime, timezone
import json
import math


class CustomerContext(BaseModel):
    """Enhanced customer context with behavioral insights and engagement metrics"""

    # ============================================
    # BEHAVIORAL INSIGHTS (Primary)
    # ============================================
    purchase_patterns: List[str] = Field(
        default_factory=list,
        description="Observable purchase behaviors: 'frequent buyer', 'price-sensitive', 'brand-loyal', etc."
    )

    review_behavior: List[str] = Field(
        default_factory=list,
        description="Review patterns: 'detailed reviewer', 'polarized reviewer', 'silent buyer', 'critical reviewer'"
    )

    product_preferences: List[str] = Field(
        default_factory=list,
        description="Category/type preferences: 'prefers premium products', 'values durability', 'tech-savvy'"
    )

    # ============================================
    # CONCERNS & EXPECTATIONS (Survey-focused)
    # ============================================
    primary_concerns: List[str] = Field(
        default_factory=list,
        description="Top 3-5 concerns from reviews/history: quality, price, durability"
    )

    expectations: List[str] = Field(
        default_factory=list,
        description="What user expects: performance, value, customer service"
    )

    pain_points: List[str] = Field(
        default_factory=list,
        description="Recurring frustrations: late delivery, poor packaging, missing features"
    )

    # ============================================
    # ENGAGEMENT METRICS
    # ============================================
    engagement_level: str = Field(
        default="unknown",
        description="User engagement: 'highly_engaged', 'moderately_engaged', 'passive_buyer', 'new_user'"
    )

    sentiment_tendency: str = Field(
        default="neutral",
        description="Review sentiment: 'positive', 'critical', 'balanced', 'polarized', 'neutral'"
    )

    review_engagement_rate: float = Field(
        default=0.0,
        description="% of purchases reviewed (0.0-1.0)"
    )

    # ============================================
    # METADATA
    # ============================================
    context_type: str = Field(
        default="demographics_only",
        description="Data source: 'exact_interaction', 'similar_products', 'demographics_only'"
    )

    confidence_score: float = Field(
        default=0.5,
        description="Confidence in context quality (0.0-1.0)"
    )

    data_points_used: int = Field(
        default=0,
        description="Number of transactions/reviews analyzed"
    )

    # ============================================
    # VALIDATORS
    # ============================================
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Confidence score must be between 0.0 and 1.0')
        return round(v, 2)

    @validator('review_engagement_rate')
    def validate_engagement_rate(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Review engagement rate must be between 0.0 and 1.0')
        return round(v, 2)

    @validator('context_type')
    def validate_context_type(cls, v):
        allowed = ['exact_interaction', 'similar_products', 'demographics_only']
        if v not in allowed:
            raise ValueError(f'context_type must be one of {allowed}')
        return v

    @validator('engagement_level')
    def validate_engagement_level(cls, v):
        allowed = ['highly_engaged', 'moderately_engaged', 'passive_buyer', 'new_user', 'unknown']
        if v not in allowed:
            raise ValueError(f'engagement_level must be one of {allowed}')
        return v

    @validator('sentiment_tendency')
    def validate_sentiment(cls, v):
        allowed = ['positive', 'critical', 'balanced', 'polarized', 'neutral']
        if v not in allowed:
            raise ValueError(f'sentiment_tendency must be one of {allowed}')
        return v


class CustomerContextAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.parser = PydanticOutputParser(pydantic_object=CustomerContext)

    def _parse_llm_response(self, response, fallback_context: CustomerContext) -> CustomerContext:
        """Parse LLM response with fallback"""
        try:
            response_text = response.content if hasattr(response, "content") else str(response)

            # Remove debug logging - only log errors
            # print(f"[CustomerContext] Parsing response ({len(response_text)} chars)")

            if response_text.startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            json_obj = json.loads(response_text)

            # Handle case where LLM returns schema format with "properties" wrapper
            if "properties" in json_obj:
                # Silently extract data from wrapper
                json_obj = json_obj.get("properties", {})

            # Remove description field if present (Pydantic schema artifact)
            if "description" in json_obj and len(json_obj) > 7:
                json_obj = {k: v for k, v in json_obj.items() if k != "description"}

            return CustomerContext(**json_obj)
        except Exception as e:
            print(f"Error parsing CustomerContext: {e}")
            print(f"[CustomerContext] Full response object: {response}")
            return fallback_context

    def generate_context(self, user_id: str, item_id: str) -> CustomerContext:
        """
        Autonomous customer context generation with 3-path decision logic

        Path 1: Exact Interaction - User purchased/reviewed THIS product (confidence: 0.85-0.95)
        Path 2: Similar Products - User has similar purchases via vector search (confidence: 0.55-0.80)
        Path 3: Demographics Only - No purchase history (confidence: 0.35-0.45)
        """
        # Get user and product from database
        user = db.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User not found with ID: {user_id}")

        # ENFORCE MAIN USER ONLY - Customer Context Agent analyzes survey target only
        if not user.get("is_main_user", False):
            raise ValueError(
                f"Customer Context Agent can only analyze main user (is_main_user=True). "
                f"User {user_id} is not the survey target."
            )

        product = db.get_product_by_id(item_id)
        if not product:
            raise ValueError(f"Product not found with ID: {item_id}")

        # PATH DECISION LOGIC
        # Path 1: Check for exact interaction
        exact_interaction = self._check_exact_interaction(user_id, item_id)
        if exact_interaction:
            return self._generate_from_exact_interaction(user, product, exact_interaction)

        # Path 2: Check for similar product purchases
        similar_interactions = self._find_similar_product_interactions(user_id, product)
        if similar_interactions:
            return self._generate_from_similar_products(user, product, similar_interactions)

        # Path 3: Fall back to demographics only
        return self._generate_from_demographics_only(user)

    def _check_exact_interaction(self, user_id: str, item_id: str) -> Dict[str, Any]:
        """
        Check if user purchased or reviewed THIS exact product
        Returns: Dict with transaction and review data, or None
        """
        # Check for purchase transaction
        transaction = db.get_user_transaction_for_product(user_id, item_id)
        if not transaction:
            return None

        # Check if user reviewed this transaction
        review = db.get_review_by_transaction_id(transaction["transaction_id"])

        return {
            "transaction": transaction,
            "review": review,
            "has_review": review is not None
        }

    def _find_similar_product_interactions(self, user_id: str, product: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find user's purchases of similar products using vector search
        Returns: List of transactions with similarity scores, ranked by relevance
        """
        product_embedding = product.get("embeddings")
        if not product_embedding:
            product_text = f"{product.get('title', '')} {product.get('description', '')}"
            product_embedding = embedding_service.generate_embedding(product_text)
        elif isinstance(product_embedding, str):
            product_embedding = json.loads(product_embedding)

        # Find similar product purchases (similarity threshold: 0.7)
        similar_transactions = db.find_user_similar_product_purchases(
            user_id, product_embedding, limit=settings.max_user_history
        )

        if not similar_transactions:
            return []

        # Get reviews for these transactions
        transaction_ids = [t["transaction_id"] for t in similar_transactions]
        reviews = db.get_reviews_by_transaction_ids(transaction_ids)
        review_map = {r["transaction_id"]: r for r in reviews}

        # Attach reviews to transactions
        for txn in similar_transactions:
            txn["review"] = review_map.get(txn["transaction_id"])
            txn["has_review"] = txn["review"] is not None

        # Rank by similarity, recency, and engagement
        ranked_transactions = self._rank_transactions_by_similarity_recency_engagement(
            similar_transactions
        )

        return ranked_transactions

    def _rank_transactions_by_similarity_recency_engagement(
        self, transactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Multi-factor ranking for similar product transactions

        Weights:
        - Similarity: 45% (vector similarity score)
        - Recency: 30% (exponential decay, 180-day half-life)
        - Engagement: 25% (has review)
        """
        now = datetime.now(timezone.utc)
        half_life_days = 180

        for txn in transactions:
            # Similarity score (already provided by database)
            similarity_score = txn.get("similarity_score", 0.7)

            # Recency score (exponential decay)
            # Find the most recent non-null date from transaction lifecycle
            date_fields = [
                txn.get("return_date"),          # Most recent if returned
                txn.get("delivery_date"),        # Recent if delivered
                txn.get("expected_delivery_date"),
                txn.get("order_date"),           # Fallback to order date
                txn.get("updated_at")            # Last fallback
            ]

            # Filter out None values and parse strings to datetime
            valid_dates = []
            for date_val in date_fields:
                if date_val is not None:
                    if isinstance(date_val, str):
                        try:
                            valid_dates.append(datetime.fromisoformat(date_val.replace('Z', '+00:00')))
                        except:
                            continue
                    elif isinstance(date_val, datetime):
                        valid_dates.append(date_val)

            # Use the most recent date for recency calculation
            if valid_dates:
                txn_date = max(valid_dates)
                days_ago = (now - txn_date).days
                recency_score = math.exp(-days_ago * math.log(2) / half_life_days)
            else:
                # If no valid dates found, assign lowest recency score
                recency_score = 0.0

            # Engagement score (binary: reviewed or not)
            engagement_score = 1.0 if txn.get("has_review") else 0.0

            # Combined score
            txn["rank_score"] = (
                0.45 * similarity_score +
                0.30 * recency_score +
                0.25 * engagement_score
            )

        # Sort by rank score (descending)
        transactions.sort(key=lambda t: t["rank_score"], reverse=True)

        return transactions

    # ============================================
    # PATH 1: EXACT INTERACTION
    # ============================================
    def _generate_from_exact_interaction(
        self, user: Dict[str, Any], product: Dict[str, Any], interaction: Dict[str, Any]
    ) -> CustomerContext:
        """
        Generate context from exact product purchase/review
        Confidence: 0.85-0.95 (highest)
        """
        transaction = interaction["transaction"]
        review = interaction.get("review")
        has_review = interaction["has_review"]

        # Build context from exact interaction
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a customer behavior analyst. This user purchased THIS EXACT PRODUCT.
Analyze their interaction with this product and their complete profile to generate customer context.

CRITICAL INSTRUCTIONS:
1. Use the Engagement Metrics to infer behavioral patterns (purchase frequency, review habits, sentiment)
2. Even without a review of THIS product, derive insights from their historical behavior metrics
3. Generate specific, actionable insights for purchase_patterns, review_behavior, product_preferences
4. Infer primary_concerns, expectations, and pain_points based on their engagement level and sentiment
5. NEVER return empty arrays - always provide at least 2-3 items per field based on available data"""),
            ("human", """User Profile:
Name: {user_name}
Age: {age}
Location: {location}
Gender: {gender}

Engagement Metrics (across ALL historical purchases):
- Total Purchases: {total_purchases}
- Total Reviews: {total_reviews}
- Review Engagement Rate: {review_engagement_rate} (what % of purchases they review)
- Avg Review Rating: {avg_review_rating}
- Sentiment Tendency: {sentiment_tendency}
- Engagement Level: {engagement_level}

EXACT PRODUCT PURCHASED:
Product: {product_title}
Brand: {brand}
Price: ${final_price}
Purchase Date: {transaction_date}
Transaction Status: {transaction_status}

{review_section}

Based on this user's EXACT interaction with this product AND their historical engagement metrics, generate comprehensive customer context.

REQUIRED OUTPUT:
- purchase_patterns: Derive from total_purchases, review_engagement_rate (e.g., "frequent buyer", "price-conscious", "selective shopper")
- review_behavior: Derive from total_reviews, review_engagement_rate, sentiment_tendency (e.g., "engaged reviewer", "silent buyer", "critical evaluator")
- product_preferences: Infer from engagement_level and demographics (e.g., "quality-focused", "brand-conscious")
- primary_concerns: Based on product category, price point, and user profile (e.g., "product quality", "value for money", "durability")
- expectations: What this user type typically expects (e.g., "reliable performance", "good customer service")
- pain_points: Common frustrations for this engagement level (e.g., "late delivery", "poor quality", "unclear product details")

{format_instructions}"""),
        ])

        # Prepare review section
        if has_review and review:
            review_section = f"""USER'S REVIEW OF THIS PRODUCT:
Rating: {review['review_stars']}/5
Title: {review.get('review_title', 'N/A')}
Review: {review['review_text']}
Date: {review.get('timestamp', 'N/A')}"""
        else:
            review_section = "USER DID NOT REVIEW THIS PRODUCT (silent purchase - no feedback provided)"

        # Prepare input data
        llm_input = {
            "user_name": user.get("user_name", "Unknown"),
            "age": user.get("age", "Unknown"),
            "location": user.get("base_location", "Unknown"),
            "gender": user.get("gender", "Unknown"),
            "total_purchases": user.get("total_purchases", 0),
            "total_reviews": user.get("total_reviews", 0),
            "review_engagement_rate": user.get("review_engagement_rate", 0.0),
            "avg_review_rating": user.get("avg_review_rating", 0.0),
            "sentiment_tendency": user.get("sentiment_tendency", "neutral"),
            "engagement_level": user.get("engagement_level", "unknown"),
            "product_title": product.get("title", "Unknown Product"),
            "brand": product.get("brand", "Unknown"),
            "final_price": transaction.get("retail_price", transaction.get("original_price", 0)),
            "transaction_date": transaction.get("order_date", transaction.get("delivery_date", "Unknown")),
            "transaction_status": transaction.get("transaction_status", "unknown"),
            "review_section": review_section,
            "format_instructions": self.parser.get_format_instructions(),
        }

        # Minimal logging - only key info
        # print(f"[CustomerContext] Analyzing user: {llm_input['user_name']}, Product: {llm_input['product_title'][:50]}...")

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke(llm_input)

        # Build intelligent fallback based on user metrics
        purchase_patterns_fallback = []
        if user.get("total_purchases", 0) >= 5:
            purchase_patterns_fallback.append("Frequent buyer")
        if user.get("review_engagement_rate", 0) < 0.3:
            purchase_patterns_fallback.append("Price-conscious shopper")

        review_behavior_fallback = []
        if user.get("review_engagement_rate", 0) >= 0.5:
            review_behavior_fallback.append("Engaged reviewer")
        elif user.get("review_engagement_rate", 0) < 0.3:
            review_behavior_fallback.append("Silent buyer")

        if user.get("avg_review_rating", 0) >= 4.0:
            review_behavior_fallback.append("Positive reviewer")

        fallback = CustomerContext(
            purchase_patterns=purchase_patterns_fallback or ["Exact product purchaser"],
            review_behavior=review_behavior_fallback or ["Selective feedback provider"],
            primary_concerns=["Product quality", "Value for money"],
            expectations=["Reliable performance", "Good customer service"],
            pain_points=["Product defects", "Delivery delays"],
            context_type="exact_interaction",
            confidence_score=0.85,
            data_points_used=1
        )
        context = self._parse_llm_response(response, fallback)

        # Minimal logging - only success confirmation
        # print(f"[CustomerContext] ✓ Context generated (confidence: {context.confidence_score})")

        # Set metadata
        context.context_type = "exact_interaction"
        context.confidence_score = 0.95 if has_review else 0.85
        context.data_points_used = 2 if has_review else 1

        # Set engagement metrics from user profile
        context.engagement_level = user.get("engagement_level", "unknown")
        context.sentiment_tendency = user.get("sentiment_tendency", "neutral")
        context.review_engagement_rate = user.get("review_engagement_rate", 0.0)

        return context

    # ============================================
    # PATH 2: SIMILAR PRODUCTS
    # ============================================
    def _generate_from_similar_products(
        self, user: Dict[str, Any], product: Dict[str, Any], similar_interactions: List[Dict[str, Any]]
    ) -> CustomerContext:
        """
        Generate context from similar product purchases
        Confidence: 0.55-0.80 (medium-high)
        """
        # Select top ranked transactions (up to 10)
        top_transactions = similar_interactions[:10]

        # Separate reviewed vs unreviewed transactions
        reviewed_txns = [t for t in top_transactions if t.get("has_review")]
        unreviewed_txns = [t for t in top_transactions if not t.get("has_review")]

        # Build transaction summary
        txn_texts = []
        for txn in top_transactions[:5]:  # Top 5 for LLM context
            product_info = txn.get("products", {})
            txn_texts.append(
                f"Product: {product_info.get('title', 'Unknown')} (Brand: {product_info.get('brand', 'Unknown')})\n"
                f"Price: ${txn.get('final_price', 0)}\n"
                f"Similarity: {txn.get('similarity_score', 0):.2f}\n"
                f"Rank Score: {txn.get('rank_score', 0):.2f}\n"
                f"Reviewed: {'Yes' if txn.get('has_review') else 'No'}"
            )

        # Build review summary
        review_texts = []
        for txn in reviewed_txns[:5]:  # Top 5 reviews
            review = txn.get("review")
            if review:
                review_texts.append(
                    f"Product: {txn.get('products', {}).get('title', 'Unknown')}\n"
                    f"Rating: {review['review_stars']}/5\n"
                    f"Review: {review['review_text'][:300]}\n"
                )

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a customer behavior analyst. This user purchased SIMILAR products (not this exact one).
Analyze their purchase patterns and reviews of similar products to infer likely concerns and expectations for THIS product.
Make intelligent inferences based on behavioral patterns from similar purchases."""),
            ("human", """User Profile:
Name: {user_name}
Age: {age}
Location: {location}
Gender: {gender}

Engagement Metrics:
- Total Purchases: {total_purchases}
- Total Reviews: {total_reviews}
- Review Engagement Rate: {review_engagement_rate}
- Avg Review Rating: {avg_review_rating}
- Sentiment Tendency: {sentiment_tendency}
- Engagement Level: {engagement_level}

TARGET PRODUCT (user has NOT purchased this):
Product: {product_title}
Brand: {brand}
Price: ${price}

SIMILAR PRODUCTS USER PURCHASED ({similar_count} total):
{similar_transactions}

{review_section}

Based on this user's purchases and reviews of SIMILAR products, infer their likely:
- Purchase patterns and preferences
- Primary concerns for this product category
- Expectations and standards
- Potential pain points

{format_instructions}"""),
        ])

        # Prepare review section
        if review_texts:
            review_section = f"USER'S REVIEWS OF SIMILAR PRODUCTS ({len(review_texts)} reviews):\n\n" + "\n\n".join(review_texts)
        else:
            review_section = "USER DID NOT REVIEW SIMILAR PRODUCTS (silent purchaser - no feedback provided)"

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke({
            "user_name": user.get("user_name", "Unknown"),
            "age": user.get("age", "Unknown"),
            "location": user.get("base_location", "Unknown"),
            "gender": user.get("gender", "Unknown"),
            "total_purchases": user.get("total_purchases", 0),
            "total_reviews": user.get("total_reviews", 0),
            "review_engagement_rate": user.get("review_engagement_rate", 0.0),
            "avg_review_rating": user.get("avg_review_rating", 0.0),
            "sentiment_tendency": user.get("sentiment_tendency", "neutral"),
            "engagement_level": user.get("engagement_level", "unknown"),
            "product_title": product.get("title", "Unknown Product"),
            "brand": product.get("brand", "Unknown"),
            "price": product.get("price", 0),
            "similar_count": len(similar_interactions),
            "similar_transactions": "\n\n".join(txn_texts),
            "review_section": review_section,
            "format_instructions": self.parser.get_format_instructions(),
        })

        fallback = CustomerContext(
            purchase_patterns=["Similar product buyer"],
            primary_concerns=["Product quality and value"],
            expectations=["Based on similar purchases"],
            context_type="similar_products",
            confidence_score=0.65,
            data_points_used=len(top_transactions)
        )
        context = self._parse_llm_response(response, fallback)

        # Set metadata
        context.context_type = "similar_products"

        # Dynamic confidence based on data quality
        base_confidence = 0.55
        review_bonus = min(0.15, len(reviewed_txns) * 0.03)  # +0.03 per review, max +0.15
        similarity_bonus = min(0.10, (similar_interactions[0].get("similarity_score", 0.7) - 0.7) / 2)  # based on top similarity
        context.confidence_score = min(0.80, base_confidence + review_bonus + similarity_bonus)

        context.data_points_used = len(top_transactions)

        # Set engagement metrics from user profile
        context.engagement_level = user.get("engagement_level", "unknown")
        context.sentiment_tendency = user.get("sentiment_tendency", "neutral")
        context.review_engagement_rate = user.get("review_engagement_rate", 0.0)

        return context

    # ============================================
    # PATH 3: DEMOGRAPHICS ONLY
    # ============================================
    def _generate_from_demographics_only(self, user: Dict[str, Any]) -> CustomerContext:
        """
        Generate context from demographics only (no purchase history)
        Confidence: 0.35-0.45 (lowest)
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a customer behavior analyst. This user has NO purchase history in our system.
Generate plausible customer context based ONLY on their demographic profile and engagement metrics.
Be realistic but acknowledge this is generic context based on demographics."""),
            ("human", """User Profile:
Name: {user_name}
Age: {age}
Location: {location}
Gender: {gender}

Engagement Metrics:
- Total Purchases: {total_purchases}
- Total Reviews: {total_reviews}
- Engagement Level: {engagement_level}

This user has NO purchase or review history. Based solely on their demographic profile, generate plausible:
- Purchase patterns and preferences (generic for this demographic)
- Primary concerns (common for this demographic)
- Expectations (typical for this demographic)
- Potential pain points (common for this demographic)

Be realistic and acknowledge the limited data available.

{format_instructions}"""),
        ])

        # Invoke LLM
        chain = prompt | self.llm
        response = chain.invoke({
            "user_name": user.get("user_name", "Unknown"),
            "age": user.get("age", "Unknown"),
            "location": user.get("base_location", "Unknown"),
            "gender": user.get("gender", "Unknown"),
            "total_purchases": user.get("total_purchases", 0),
            "total_reviews": user.get("total_reviews", 0),
            "engagement_level": user.get("engagement_level", "new_user"),
            "format_instructions": self.parser.get_format_instructions(),
        })

        fallback = CustomerContext(
            purchase_patterns=["New user - no purchase history"],
            primary_concerns=["General consumer concerns"],
            expectations=["Standard expectations"],
            pain_points=["No historical data available"],
            context_type="demographics_only",
            confidence_score=0.35,
            data_points_used=0
        )
        context = self._parse_llm_response(response, fallback)

        # Set metadata
        context.context_type = "demographics_only"
        context.confidence_score = 0.35  # Low confidence for demographics-only
        context.data_points_used = 0

        # Set engagement metrics from user profile
        context.engagement_level = user.get("engagement_level", "new_user")
        context.sentiment_tendency = user.get("sentiment_tendency", "neutral")
        context.review_engagement_rate = user.get("review_engagement_rate", 0.0)

        return context


customer_context_agent = CustomerContextAgent()