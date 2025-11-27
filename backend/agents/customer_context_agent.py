"""
Agent 2: Customer context generation from review/purchase history or demographics.
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from config import settings
from database import db
from utils import embedding_service
import json


class CustomerContext(BaseModel):
    major_concerns: List[str] = Field(default_factory=list)
    expectations: List[str] = Field(default_factory=list)
    purchase_motivations: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    user_segment: str = Field(default="general_user")
    context_type: str = Field(default="demographic")
    confidence_score: float = Field(default=0.5)


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

            print(f"[CustomerContext] Response type: {type(response)}")
            print(f"[CustomerContext] Response has content attr: {hasattr(response, 'content')}")
            print(f"[CustomerContext] Response text length: {len(response_text) if response_text else 0}")
            print(f"[CustomerContext] Response text preview: {response_text[:500] if response_text else 'EMPTY'}")

            if response_text.startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            json_obj = json.loads(response_text)

            if "description" in json_obj and len(json_obj) > 7:
                json_obj = {k: v for k, v in json_obj.items() if k != "description"}

            return CustomerContext(**json_obj)
        except Exception as e:
            print(f"Error parsing CustomerContext: {e}")
            print(f"[CustomerContext] Full response object: {response}")
            return fallback_context

    def generate_context(self, user_email: str, item_id: str, has_purchased_similar: bool, form_data: Dict[str, Any]) -> CustomerContext:
        """Generate customer context from history or demographics"""
        user = db.get_user_by_email(user_email)
        if not user:
            return self._generate_from_persona_only(form_data)

        product = db.get_product_by_id(item_id)
        if not product:
            raise ValueError(f"Product not found with ID: {item_id}")

        if has_purchased_similar:
            return self._generate_from_purchase_history(user, product, form_data)
        else:
            return self._generate_from_demographics(user)

    def _generate_from_purchase_history(self, user: Dict[str, Any], product: Dict[str, Any], form_data: Dict[str, Any]) -> CustomerContext:
        """Generate context from purchase and review history"""
        product_embedding = product.get("embeddings")
        if not product_embedding:
            product_text = f"{product.get('title', '')} {product.get('description', '')}"
            product_embedding = embedding_service.generate_embedding(product_text)
        elif isinstance(product_embedding, str):
            import json
            product_embedding = json.loads(product_embedding)

        similar_transactions = db.find_user_similar_product_purchases(
            user["user_id"], product_embedding, limit=settings.max_user_history
        )

        user_reviews = db.get_user_reviews(user["user_id"], limit=20)

        reviewed_similar_items = set()
        for review in user_reviews:
            if review.get("item_id") in [txn["item_id"] for txn in similar_transactions]:
                reviewed_similar_items.add(review["item_id"])

        if reviewed_similar_items:
            return self._generate_from_review_history(user, user_reviews, similar_transactions)
        else:
            return self._generate_from_transactions_only(user, similar_transactions, user_reviews)

    def _generate_from_review_history(self, user: Dict[str, Any], user_reviews: List[Dict[str, Any]], similar_transactions: List[Dict[str, Any]]) -> CustomerContext:
        """Extract concerns from user's review history"""
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

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a customer behavior analyst. Analyze this user's review history to understand their:
- Major concerns when buying products
- Expectations and standards
- What motivates their purchases
- Common pain points

Extract real patterns from their reviews. Be specific and actionable."""),
            ("human", """User Profile:
Name: {name}
Age: {age}
Location: {location}
Gender: {gender}

Purchase History: {transaction_count} transactions
Review History: {review_count} reviews

User's Past Reviews:
{reviews}

Analyze this user's review history and purchase patterns. What are their major concerns, expectations, and pain points?

{format_instructions}"""),
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "name": user.get("name", "Unknown"),
            "age": user.get("age", "Unknown"),
            "location": user.get("location", "Unknown"),
            "gender": user.get("gender", "Unknown"),
            "transaction_count": len(similar_transactions),
            "review_count": len(user_reviews),
            "reviews": review_summary,
            "format_instructions": self.parser.get_format_instructions(),
        })

        fallback = CustomerContext(
            major_concerns=["Product quality and value"],
            expectations=["Good performance"],
            purchase_motivations=["Based on review history"],
            pain_points=["Limited data"],
            user_segment="review_based",
            context_type="review_history",
            confidence_score=0.5
        )
        context = self._parse_llm_response(response, fallback)

        context.context_type = "review_history"
        context.confidence_score = min(0.9, 0.6 + (len(user_reviews) / 40))

        return context

    def _generate_from_transactions_only(self, user: Dict[str, Any], similar_transactions: List[Dict[str, Any]], user_reviews: List[Dict[str, Any]]) -> CustomerContext:
        """Derive expectations from purchase history"""
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

        # Generate context with manual parsing
        chain = prompt | self.llm
        response = chain.invoke(
            {
                "name": user.get("name", "Unknown"),
                "age": user.get("age", "Unknown"),
                "location": user.get("location", "Unknown"),
                "transactions": txn_summary,
                "other_reviews": other_reviews_summary,
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        fallback = CustomerContext(
            major_concerns=["Product reliability"],
            expectations=["Consistent quality"],
            purchase_motivations=["Based on past purchases"],
            pain_points=["Limited feedback"],
            user_segment="purchase_based",
            context_type="purchase_history",
            confidence_score=0.5
        )
        context = self._parse_llm_response(response, fallback)

        context.context_type = "purchase_history"
        context.confidence_score = min(0.7, 0.5 + (len(similar_transactions) / 20))

        return context

    def _generate_from_demographics(self, user: Dict[str, Any]) -> CustomerContext:
        """Generate context from demographics"""
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

        # Generate context with manual parsing
        chain = prompt | self.llm
        response = chain.invoke(
            {
                "name": user.get("name", "Unknown"),
                "age": user.get("age", "Unknown"),
                "location": user.get("location", "Unknown"),
                "gender": user.get("gender", "Unknown"),
                "income_level": user.get("income_level", "median"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        fallback = CustomerContext(
            major_concerns=["General consumer concerns"],
            expectations=["Standard expectations"],
            purchase_motivations=["Based on demographics"],
            pain_points=["No purchase history"],
            user_segment="new_user",
            context_type="demographic",
            confidence_score=0.5
        )
        context = self._parse_llm_response(response, fallback)

        context.context_type = "demographic"
        context.confidence_score = 0.5  # Medium confidence for demographic-only context

        return context

    def _generate_from_persona_only(self, form_data: Dict[str, Any]) -> CustomerContext:
        """Generate context from form persona data only"""
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

        # Generate context with manual parsing
        chain = prompt | self.llm
        response = chain.invoke(
            {
                "name": persona.get("name", "Unknown"),
                "email": persona.get("email", "unknown@example.com"),
                "age": persona.get("age", "Unknown"),
                "location": persona.get("location", "Unknown"),
                "format_instructions": self.parser.get_format_instructions(),
            }
        )

        fallback = CustomerContext(
            major_concerns=["General new user concerns"],
            expectations=["Basic expectations"],
            purchase_motivations=["Based on persona"],
            pain_points=["No historical data"],
            user_segment="new_user",
            context_type="demographic",
            confidence_score=0.3
        )
        context = self._parse_llm_response(response, fallback)

        context.context_type = "demographic"
        context.confidence_score = 0.3  # Low confidence for persona-only context

        return context


customer_context_agent = CustomerContextAgent()