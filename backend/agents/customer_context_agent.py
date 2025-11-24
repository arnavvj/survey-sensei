"""
Agent 2: CUSTOMER_CONTEXT_AGENT
Stateless LangChain agent for generating customer/user-related context

Workflow:
1. Check if user purchased similar products
   Yes → Check if user reviewed similar products
         Yes → Extract user's concerns/expectations from their reviews
         No  → Analyze purchase history and derive expectations
   No  → Generate generic context based on user demographics
2. Generate customer context (concerns, requirements, expectations)
3. Return context to Agent 3
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from config import settings
from database import db
from utils import embedding_service


class CustomerContext(BaseModel):
    """Structured customer context output"""

    major_concerns: List[str] = Field(
        description="Major concerns or requirements this user has when purchasing products"
    )
    expectations: List[str] = Field(
        description="User's expectations based on their history and persona"
    )
    purchase_motivations: List[str] = Field(
        description="What motivates this user to make purchases (price, quality, features, etc.)"
    )
    pain_points: List[str] = Field(
        description="Common pain points or frustrations from user's review history"
    )
    user_segment: str = Field(
        description="User segment: budget_conscious, quality_seeker, feature_focused, brand_loyal, etc."
    )
    context_type: str = Field(
        description="Type of context: 'review_history', 'purchase_history', or 'demographic'"
    )
    confidence_score: float = Field(
        description="Confidence score 0-1 based on available data"
    )


class CustomerContextAgent:
    """Agent 2: Generates customer-related context for survey generation"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.parser = PydanticOutputParser(pydantic_object=CustomerContext)

    def generate_context(
        self,
        user_email: str,
        item_id: str,
        has_purchased_similar: bool,
        form_data: Dict[str, Any],
    ) -> CustomerContext:
        """
        Main entry point: Generate customer context based on available data

        Args:
            user_email: User's email from form
            item_id: Product ID being surveyed
            has_purchased_similar: Whether user purchased similar products (from form)
            form_data: Complete form submission data

        Returns:
            CustomerContext with structured insights
        """
        # Get user from database
        user = db.get_user_by_email(user_email)
        if not user:
            # Create user context from form persona data
            return self._generate_from_persona_only(form_data)

        # Get product for similarity search
        product = db.get_product_by_id(item_id)
        if not product:
            raise ValueError(f"Product not found with ID: {item_id}")

        # Branch based on purchase history
        if has_purchased_similar:
            return self._generate_from_purchase_history(user, product, form_data)
        else:
            return self._generate_from_demographics(user)

    def _generate_from_purchase_history(
        self, user: Dict[str, Any], product: Dict[str, Any], form_data: Dict[str, Any]
    ) -> CustomerContext:
        """
        Scenario 1: User has purchased similar products
        Check if they reviewed them, then generate context
        """
        # Get product embedding
        product_embedding = product.get("embeddings")
        if not product_embedding:
            product_text = f"{product.get('title', '')} {product.get('description', '')}"
            product_embedding = embedding_service.generate_embedding(product_text)
        elif isinstance(product_embedding, str):
            # Parse if stored as JSON string
            import json
            product_embedding = json.loads(product_embedding)

        # Find user's similar product purchases
        similar_transactions = db.find_user_similar_product_purchases(
            user["user_id"], product_embedding, limit=settings.max_user_history
        )

        # Get user's review history
        user_reviews = db.get_user_reviews(user["user_id"], limit=20)

        # Check if user reviewed similar products
        reviewed_similar_items = set()
        for review in user_reviews:
            if review.get("item_id") in [
                txn["item_id"] for txn in similar_transactions
            ]:
                reviewed_similar_items.add(review["item_id"])

        if reviewed_similar_items:
            # Scenario 1a: User reviewed similar products
            return self._generate_from_review_history(
                user, user_reviews, similar_transactions
            )
        else:
            # Scenario 1b: User purchased but didn't review
            return self._generate_from_transactions_only(
                user, similar_transactions, user_reviews
            )

    def _generate_from_review_history(
        self,
        user: Dict[str, Any],
        user_reviews: List[Dict[str, Any]],
        similar_transactions: List[Dict[str, Any]],
    ) -> CustomerContext:
        """
        Scenario 1a: User has reviewed similar products
        Extract concerns and expectations from review history
        """
        # Prepare review data
        review_texts = []
        for review in user_reviews[:15]:
            product_title = review.get("products", {}).get("title", "Unknown Product")
            review_texts.append(
                f"Product: {product_title}\n"
                f"Rating: {review['review_stars']}/5\n"
                f"Review: {review['review_text']}\n"
                f"Sentiment: {review.get('sentiment_label', 'neutral')}"
            )

        review_summary = "\n\n".join(review_texts)

        # Create prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a customer behavior analyst. Analyze this user's review history to understand their:
- Major concerns when buying products
- Expectations and standards
- What motivates their purchases
- Common pain points

Extract real patterns from their reviews. Be specific and actionable.""",
                ),
                (
                    "human",
                    """User Profile:
Name: {name}
Age: {age}
Location: {location}
Gender: {gender}

Purchase History: {transaction_count} transactions
Review History: {review_count} reviews

User's Past Reviews:
{reviews}

Analyze this user's review history and purchase patterns. What are their major concerns, expectations, and pain points?

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser
        context = chain.invoke(
            {
                "name": user.get("name", "Unknown"),
                "age": user.get("age", "Unknown"),
                "location": user.get("location", "Unknown"),
                "gender": user.get("gender", "Unknown"),
                "transaction_count": len(similar_transactions),
                "review_count": len(user_reviews),
                "reviews": review_summary,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "review_history"
        context.confidence_score = min(0.9, 0.6 + (len(user_reviews) / 40))

        return context

    def _generate_from_transactions_only(
        self,
        user: Dict[str, Any],
        similar_transactions: List[Dict[str, Any]],
        user_reviews: List[Dict[str, Any]],
    ) -> CustomerContext:
        """
        Scenario 1b: User purchased similar products but didn't review them
        Derive expectations from purchase history and any other reviews
        """
        # Prepare transaction data
        transaction_texts = []
        for txn in similar_transactions[:10]:
            product = txn.get("products", {})
            transaction_texts.append(
                f"Product: {product.get('title', 'Unknown')}\n"
                f"Price: ${txn.get('final_price', 0)}\n"
                f"Status: {txn.get('transaction_status', 'unknown')}\n"
                f"Similarity: {txn.get('similarity_score', 0):.2f}"
            )

        txn_summary = "\n\n".join(transaction_texts)

        # Prepare any reviews user has written (for other products)
        other_review_texts = []
        if user_reviews:
            for review in user_reviews[:10]:
                other_review_texts.append(
                    f"Rating: {review['review_stars']}/5 | {review['review_text'][:200]}"
                )

        other_reviews_summary = (
            "\n".join(other_review_texts) if other_review_texts else "No reviews found"
        )

        # Create prompt
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a customer behavior analyst. This user purchased similar products but didn't review them.
Analyze their purchase patterns and any other reviews to infer their likely concerns and expectations.
Make educated inferences based on purchase behavior.""",
                ),
                (
                    "human",
                    """User Profile:
Name: {name}
Age: {age}
Location: {location}

Similar Product Purchases:
{transactions}

Other Reviews by This User:
{other_reviews}

This user purchased similar products but didn't review them. Based on their purchase history and other reviews,
what are their likely concerns, expectations, and motivations?

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser
        context = chain.invoke(
            {
                "name": user.get("name", "Unknown"),
                "age": user.get("age", "Unknown"),
                "location": user.get("location", "Unknown"),
                "transactions": txn_summary,
                "other_reviews": other_reviews_summary,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "purchase_history"
        context.confidence_score = min(0.7, 0.5 + (len(similar_transactions) / 20))

        return context

    def _generate_from_demographics(self, user: Dict[str, Any]) -> CustomerContext:
        """
        Scenario 2: User has no similar purchase history
        Generate generic context based on demographics
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a customer behavior analyst. This user has no similar purchase history.
Generate plausible concerns and expectations based on their demographic profile.
Use age, location, gender, and other demographics to infer likely preferences.""",
                ),
                (
                    "human",
                    """User Profile:
Name: {name}
Age: {age}
Location: {location}
Gender: {gender}
Income Level: {income_level}

This user has no similar purchase history. Based on their demographic profile, what are their likely:
- Concerns when purchasing products
- Expectations and standards
- Purchase motivations
- Common pain points

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser
        context = chain.invoke(
            {
                "name": user.get("name", "Unknown"),
                "age": user.get("age", "Unknown"),
                "location": user.get("location", "Unknown"),
                "gender": user.get("gender", "Unknown"),
                "income_level": user.get("income_level", "median"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "demographic"
        context.confidence_score = 0.5  # Medium confidence for demographic-only context

        return context

    def _generate_from_persona_only(self, form_data: Dict[str, Any]) -> CustomerContext:
        """
        Scenario 3: New user with no existing transactions in the database.
        Context should be generated solely from the persona data provided in the form.
        """
        persona = form_data.get("userPersona", {})

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a customer behavior analyst. This is a new user with no history.
Generate plausible concerns and expectations based solely on their basic profile.
Be realistic but acknowledge this is generic context.""",
                ),
                (
                    "human",
                    """New User Profile:
Name: {name}
Email: {email}
Age: {age}
Location: {location}

This is a new user with no purchase or review history. Based on their profile, generate generic but plausible:
- Concerns when purchasing products
- Expectations
- Likely purchase motivations
- Potential pain points

{format_instructions}""",
                ),
            ]
        )

        # Generate context
        chain = prompt | self.llm | self.parser
        context = chain.invoke(
            {
                "name": persona.get("name", "Unknown"),
                "email": persona.get("email", "unknown@example.com"),
                "age": persona.get("age", "Unknown"),
                "location": persona.get("location", "Unknown"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        context.context_type = "demographic"
        context.confidence_score = 0.3  # Low confidence for persona-only context

        return context


# Global agent instance
customer_context_agent = CustomerContextAgent()