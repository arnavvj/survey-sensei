"""
Agent 1: Product context generation from reviews or product description.
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
    major_concerns: List[str] = Field(default_factory=list)
    key_features: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    common_use_cases: List[str] = Field(default_factory=list)
    context_type: str = Field(default="generic")
    confidence_score: float = Field(default=0.5)


class ProductContextAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.parser = PydanticOutputParser(pydantic_object=ProductContext)

    def generate_context(self, item_id: str, has_reviews: bool, form_data: Dict[str, Any]) -> ProductContext:
        """Generate product context from reviews or description"""
        product = db.get_product_by_id(item_id)
        if not product:
            raise ValueError(f"Product not found with ID: {item_id}")

        if has_reviews:
            return self._generate_from_direct_reviews(product)
        else:
            return self._generate_from_similar_or_generic(product, form_data)

    def _generate_from_direct_reviews(self, product: Dict[str, Any]) -> ProductContext:
        """Extract context from product's reviews"""
        reviews = db.get_product_reviews(product["item_id"], limit=50)

        if not reviews:
            return self._generate_generic_context(product)

        review_texts = [
            f"Rating: {r['review_stars']}/5 | {r['review_text']}" for r in reviews[:30]
        ]
        review_summary = "\n".join(review_texts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product analysis expert. Analyze the product and its reviews to extract key insights.
Focus on: Major concerns, key features, pros/cons, and common use cases. Be specific and actionable."""),
            ("human", """Product: {title}
Description: {description}
Brand: {brand}

Reviews ({review_count} total):
{reviews}

Analyze this product and its reviews. Extract the most important insights for generating a personalized survey.

{format_instructions}"""),
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "title": product.get("title", "Unknown"),
            "description": product.get("description", "No description"),
            "brand": product.get("brand", "Unknown"),
            "review_count": len(reviews),
            "reviews": review_summary,
            "format_instructions": self.parser.get_format_instructions(),
        })

        try:
            response_text = response.content if hasattr(response, "content") else str(response)

            print(f"[ProductContext] Response type: {type(response)}")
            print(f"[ProductContext] Response has content attr: {hasattr(response, 'content')}")
            print(f"[ProductContext] Response text length: {len(response_text) if response_text else 0}")
            print(f"[ProductContext] Response text preview: {response_text[:500] if response_text else 'EMPTY'}")

            if response_text.startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            json_obj = json.loads(response_text)

            if "description" in json_obj and len(json_obj) > 7:
                json_obj = {k: v for k, v in json_obj.items() if k != "description"}

            context = ProductContext(**json_obj)
        except Exception as e:
            print(f"Error parsing ProductContext: {e}")
            print(f"[ProductContext] Full response object: {response}")
            context = ProductContext(
                major_concerns=["Unable to analyze"],
                key_features=["Unable to analyze"],
                pros=["Unable to analyze"],
                cons=["Unable to analyze"],
                common_use_cases=["General use"],
                context_type="direct_reviews",
                confidence_score=0.3
            )

        context.context_type = "direct_reviews"
        context.confidence_score = min(0.9, 0.6 + (len(reviews) / 100))

        return context

    def _generate_from_similar_or_generic(self, product: Dict[str, Any], form_data: Dict[str, Any]) -> ProductContext:
        """Check for similar products with reviews or use generic context"""
        product_embedding = product.get("embeddings")
        if not product_embedding:
            product_text = f"{product.get('title', '')} {product.get('description', '')}"
            product_embedding = embedding_service.generate_embedding(product_text)
        elif isinstance(product_embedding, str):
            product_embedding = json.loads(product_embedding)

        similar_products = db.get_similar_products_with_reviews(
            product_embedding, limit=settings.max_similar_products
        )

        if similar_products and form_data.get("hasSimilarProductsReviewed") == "yes":
            return self._generate_from_similar_products(product, similar_products)
        else:
            return self._generate_generic_context(product)

    def _generate_from_similar_products(self, product: Dict[str, Any], similar_products: List[Dict[str, Any]]) -> ProductContext:
        """Use similar products' reviews to infer context"""
        all_reviews = []
        for sim_product in similar_products:
            reviews = sim_product.get("reviews", [])
            for review in reviews[:10]:
                all_reviews.append({
                    "product": sim_product["title"],
                    "rating": review["review_stars"],
                    "text": review["review_text"],
                })

        review_texts = [
            f"[{r['product']}] Rating: {r['rating']}/5 | {r['text']}"
            for r in all_reviews[:40]
        ]
        review_summary = "\n".join(review_texts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product analysis expert analyzing a product with no reviews yet.
Use reviews from similar products to infer likely concerns, features, and patterns."""),
            ("human", """Target Product: {title}
Description: {description}
Brand: {brand}

Similar Products with Reviews:
{similar_products}

Reviews from Similar Products:
{reviews}

Based on these similar products, infer the likely concerns, features, pros/cons, and use cases for the target product.

{format_instructions}"""),
        ])

        chain = prompt | self.llm

        similar_product_list = "\n".join(
            [f"- {p['title']} (similarity: {p.get('similarity', 0):.2f})" for p in similar_products]
        )

        response = chain.invoke({
            "title": product.get("title", "Unknown"),
            "description": product.get("description", "No description"),
            "brand": product.get("brand", "Unknown"),
            "similar_products": similar_product_list,
            "reviews": review_summary,
            "format_instructions": self.parser.get_format_instructions(),
        })

        try:
            response_text = response.content if hasattr(response, "content") else str(response)

            if response_text.startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            json_obj = json.loads(response_text)

            if "description" in json_obj and len(json_obj) > 7:
                json_obj = {k: v for k, v in json_obj.items() if k != "description"}

            context = ProductContext(**json_obj)
        except Exception as e:
            print(f"Error parsing ProductContext: {e}")
            context = ProductContext(
                major_concerns=["General product concerns"],
                key_features=["Similar to category standards"],
                pros=["Based on similar products"],
                cons=["Limited direct feedback"],
                common_use_cases=["General use"],
                context_type="similar_products",
                confidence_score=0.5
            )

        context.context_type = "similar_products"
        context.confidence_score = min(0.75, 0.5 + (len(all_reviews) / 80))

        return context

    def _generate_generic_context(self, product: Dict[str, Any]) -> ProductContext:
        """Generate context from product description only"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product analysis expert analyzing a product with no reviews.
Use the product description to generate plausible concerns, features, and insights."""),
            ("human", """Product: {title}
Description: {description}
Brand: {brand}

This product has no reviews yet. Based on the description, generate:
- Likely concerns users might have
- Key features and benefits
- Probable pros and cons
- Common use cases

{format_instructions}"""),
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "title": product.get("title", "Unknown"),
            "description": product.get("description", "No description"),
            "brand": product.get("brand", "Unknown"),
            "format_instructions": self.parser.get_format_instructions(),
        })

        try:
            response_text = response.content if hasattr(response, "content") else str(response)

            if response_text.startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            json_obj = json.loads(response_text)

            if "description" in json_obj and len(json_obj) > 7:
                json_obj = {k: v for k, v in json_obj.items() if k != "description"}

            context = ProductContext(**json_obj)
        except Exception as e:
            print(f"Error parsing ProductContext: {e}")
            context = ProductContext(
                major_concerns=["General concerns for this category"],
                key_features=["Based on product description"],
                pros=["Inferred from description"],
                cons=["No user feedback available"],
                common_use_cases=["General use"],
                context_type="generic",
                confidence_score=0.4
            )

        context.context_type = "generic"
        context.confidence_score = 0.4

        return context


product_context_agent = ProductContextAgent()
