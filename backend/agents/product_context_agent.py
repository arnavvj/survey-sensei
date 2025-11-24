"""
Agent 1: PRODUCT_CONTEXT_AGENT
Stateless LangChain agent for generating product-related context

Workflow:
1. Check if product has been reviewed
   Yes → Extract data from product's reviews
   No  → Check if similar products reviewed
         Yes → Use similar products' reviews
         No  → Use product description only
2. Generate product context (concerns, pros, cons, features)
3. Return context to Agent 3
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from config import settings
from database import db
from utils import embedding_service
import json


class ProductContext(BaseModel):
    """Structured product context output"""

    major_concerns: List[str] = Field(
        description="Major concerns or issues users have with this product/category"
    )
    key_features: List[str] = Field(
        description="Key features and benefits highlighted in reviews or description"
    )
    pros: List[str] = Field(description="Positive aspects of the product")
    cons: List[str] = Field(description="Negative aspects or shortcomings")
    common_use_cases: List[str] = Field(
        description="Common use cases or scenarios where this product is used"
    )
    context_type: str = Field(
        description="Type of context: 'direct_reviews', 'similar_products', or 'generic'"
    )
    confidence_score: float = Field(
        description="Confidence score 0-1 based on available data"
    )


class ProductContextAgent:
    """Agent 1: Generates product-related context for survey generation"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
            model_kwargs={"response_format": {"type": "json_object"}},  # Force JSON output
        )
        self.parser = PydanticOutputParser(pydantic_object=ProductContext)

    def generate_context(
        self, item_id: str, has_reviews: bool, form_data: Dict[str, Any]
    ) -> ProductContext:
        """
        Main entry point: Generate product context based on available data

        Args:
            item_id: Product ID (item_id)
            has_reviews: Whether product has reviews (from form)
            form_data: Complete form submission data

        Returns:
            ProductContext with structured insights
        """
        # Get product from database
        product = db.get_product_by_id(item_id)
        if not product:
            raise ValueError(f"Product not found with ID: {item_id}")

        # Branch based on review availability
        if has_reviews:
            return self._generate_from_direct_reviews(product)
        else:
            # Check if similar products have reviews
            return self._generate_from_similar_or_generic(product, form_data)

    def _generate_from_direct_reviews(self, product: Dict[str, Any]) -> ProductContext:
        """
        Scenario 1: Product has reviews
        Extract context from product's own reviews
        """
        # Get product reviews
        reviews = db.get_product_reviews(product["item_id"], limit=50)

        if not reviews:
            # Fallback to generic if no reviews found despite form saying yes
            return self._generate_generic_context(product)

        # Prepare review data for LLM
        review_texts = [
            f"Rating: {r['review_stars']}/5 | {r['review_text']}" for r in reviews[:30]
        ]
        review_summary = "\n".join(review_texts)

        # Create prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a product analysis expert. Analyze the product and its reviews to extract key insights.
Focus on:
- Major concerns users have
- Key features they appreciate
- Pros and cons
- Common use cases

Be specific and actionable. Extract real insights from the reviews.

IMPORTANT: You must respond with valid JSON matching the exact schema provided in the format instructions.""",
                ),
                (
                    "human",
                    """Product: {title}
Description: {description}
Brand: {brand}

Reviews ({review_count} total):
{reviews}

Analyze this product and its reviews. Extract the most important insights that would help generate a personalized survey.

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser
        context = chain.invoke(
            {
                "title": product.get("title", "Unknown"),
                "description": product.get("description", "No description"),
                "brand": product.get("brand", "Unknown"),
                "review_count": len(reviews),
                "reviews": review_summary,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "direct_reviews"
        context.confidence_score = min(0.9, 0.6 + (len(reviews) / 100))

        return context

    def _generate_from_similar_or_generic(
        self, product: Dict[str, Any], form_data: Dict[str, Any]
    ) -> ProductContext:
        """
        Scenario 2: Product has no reviews
        Check for similar products with reviews, otherwise use generic context
        """
        # Get product embedding
        product_embedding = product.get("embeddings")
        if not product_embedding:
            # Generate embedding if not exists
            product_text = f"{product.get('title', '')} {product.get('description', '')}"
            product_embedding = embedding_service.generate_embedding(product_text)
        elif isinstance(product_embedding, str):
            # Parse if stored as JSON string
            product_embedding = json.loads(product_embedding)

        # Find similar products with reviews
        similar_products = db.get_similar_products_with_reviews(
            product_embedding, limit=settings.max_similar_products
        )

        if similar_products and form_data.get("hasSimilarProductsReviewed") == "yes":
            return self._generate_from_similar_products(product, similar_products)
        else:
            return self._generate_generic_context(product)

    def _generate_from_similar_products(
        self, product: Dict[str, Any], similar_products: List[Dict[str, Any]]
    ) -> ProductContext:
        """
        Scenario 2a: Similar products have reviews
        Use similar products' reviews to infer context
        """
        # Aggregate reviews from similar products
        all_reviews = []
        for sim_product in similar_products:
            reviews = sim_product.get("reviews", [])
            for review in reviews[:10]:  # Top 10 reviews per product
                all_reviews.append(
                    {
                        "product": sim_product["title"],
                        "rating": review["review_stars"],
                        "text": review["review_text"],
                    }
                )

        # Prepare review summary
        review_texts = [
            f"[{r['product']}] Rating: {r['rating']}/5 | {r['text']}"
            for r in all_reviews[:40]
        ]
        review_summary = "\n".join(review_texts)

        # Create prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a product analysis expert. You're analyzing a product that has no reviews yet.
Use reviews from similar products to infer likely concerns, features, and patterns.
Be specific but acknowledge this is based on similar products, not direct reviews.""",
                ),
                (
                    "human",
                    """Target Product: {title}
Description: {description}
Brand: {brand}

Similar Products with Reviews:
{similar_products}

Reviews from Similar Products:
{reviews}

Based on these similar products, infer the likely concerns, features, pros/cons, and use cases for the target product.

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser

        similar_product_list = "\n".join(
            [f"- {p['title']} (similarity: {p.get('similarity', 0):.2f})" for p in similar_products]
        )

        context = chain.invoke(
            {
                "title": product.get("title", "Unknown"),
                "description": product.get("description", "No description"),
                "brand": product.get("brand", "Unknown"),
                "similar_products": similar_product_list,
                "reviews": review_summary,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "similar_products"
        context.confidence_score = min(0.75, 0.5 + (len(all_reviews) / 80))

        return context

    def _generate_generic_context(self, product: Dict[str, Any]) -> ProductContext:
        """
        Scenario 2b: No reviews available (cold start)
        Generate context based only on product description
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a product analysis expert. You're analyzing a product with no reviews.
Use the product description to generate plausible concerns, features, and insights.
Be realistic but acknowledge this is generic context without user feedback.

IMPORTANT: You must respond with valid JSON matching the exact schema provided in the format instructions.""",
                ),
                (
                    "human",
                    """Product: {title}
Description: {description}
Brand: {brand}

This product has no reviews yet. Based on the description, generate:
- Likely concerns users might have
- Key features and benefits
- Probable pros and cons
- Common use cases

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser
        context = chain.invoke(
            {
                "title": product.get("title", "Unknown"),
                "description": product.get("description", "No description"),
                "brand": product.get("brand", "Unknown"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "generic"
        context.confidence_score = 0.4  # Low confidence for generic context

        return context


# Global agent instance
product_context_agent = ProductContextAgent()
