"""
Agent 4: REVIEW_GEN_AGENT
Stateless LangChain agent for generating review options based on survey responses

Workflow:
1. Analyze survey responses for overall sentiment (good/okay/bad)
2. Determine appropriate star ratings based on sentiment band
3. Generate 2-3 natural review options with varying tones
4. Return review options to Agent 3 / API endpoint

Star Rating Logic:
- "good" band → 2 options (5 star, 4 star)
- "okay" band → 3 options (4 star, 3 star, 2 star)
- "bad" band → 2 options (2 star, 1 star)
"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from config import settings
import json


class SentimentAnalysis(BaseModel):
    """Structured sentiment analysis output"""

    sentiment_band: str = Field(
        description="Overall sentiment: 'good', 'okay', or 'bad'"
    )
    confidence_score: float = Field(
        description="Confidence in sentiment classification (0-1)"
    )
    key_positive_points: List[str] = Field(
        description="Key positive aspects mentioned in survey"
    )
    key_negative_points: List[str] = Field(
        description="Key negative aspects or concerns mentioned"
    )
    overall_satisfaction: str = Field(
        description="Brief summary of overall user satisfaction"
    )


class WritingStyleAnalysis(BaseModel):
    """Analysis of user's writing style from previous reviews"""

    has_previous_reviews: bool = Field(
        description="Whether user has written previous reviews", default=True
    )
    avg_review_length: int = Field(
        description="Average number of words in user's reviews", default=0
    )
    common_phrases: List[str] = Field(
        description="Common phrases or patterns the user uses", default_factory=list
    )
    tone_characteristics: List[str] = Field(
        description="User's typical writing tone (formal/casual, detailed/brief, etc.)",
        default_factory=list,
    )
    vocabulary_level: str = Field(
        description="Vocabulary complexity: 'simple', 'moderate', 'advanced'",
        default="moderate",
    )
    writing_style_summary: str = Field(
        description="Brief summary of user's unique writing style",
        default="User has a conversational writing style",
    )


class ReviewOption(BaseModel):
    """Single review option with star rating"""

    review_text: str = Field(description="Natural language review text")
    review_stars: int = Field(description="Star rating 1-5")
    tone: str = Field(
        description="Tone of review: 'enthusiastic', 'balanced', 'critical', etc."
    )
    highlights: List[str] = Field(
        description="Key points highlighted in this review"
    )


class ReviewOptions(BaseModel):
    """Complete set of review options"""

    reviews: List[ReviewOption] = Field(
        description="2-3 review options based on sentiment"
    )
    sentiment_band: str = Field(description="Sentiment band: good/okay/bad")


class ReviewGenAgent:
    """Agent 4: Generates intelligent review options based on survey responses"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.openai_api_key,
        )
        self.sentiment_parser = PydanticOutputParser(pydantic_object=SentimentAnalysis)
        self.writing_style_parser = PydanticOutputParser(
            pydantic_object=WritingStyleAnalysis
        )
        self.review_parser = PydanticOutputParser(pydantic_object=ReviewOptions)

    def generate_reviews(
        self,
        survey_responses: List[Dict[str, Any]],
        product_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        product_title: str,
        user_reviews: Optional[List[Dict[str, Any]]] = None,
    ) -> ReviewOptions:
        """
        Main entry point: Generate review options based on survey responses

        Args:
            survey_responses: List of Q&A pairs from survey
            product_context: Context from Agent 1
            customer_context: Context from Agent 2
            product_title: Product name
            user_reviews: Optional list of user's previous reviews for writing style analysis

        Returns:
            ReviewOptions with 2-3 review choices and appropriate star ratings
        """
        # Step 1: Analyze sentiment
        sentiment = self._analyze_sentiment(survey_responses, product_title)

        # Step 2: Analyze user's writing style if previous reviews exist
        writing_style = None
        if user_reviews and len(user_reviews) > 0:
            writing_style = self._analyze_writing_style(user_reviews)

        # Step 3: Generate reviews based on sentiment band and writing style
        reviews = self._generate_review_options(
            sentiment=sentiment,
            survey_responses=survey_responses,
            product_context=product_context,
            customer_context=customer_context,
            product_title=product_title,
            writing_style=writing_style,
        )

        return reviews

    def _analyze_sentiment(
        self, survey_responses: List[Dict[str, Any]], product_title: str
    ) -> SentimentAnalysis:
        """
        Analyze overall sentiment from survey responses

        Args:
            survey_responses: List of Q&A pairs
            product_title: Product name

        Returns:
            SentimentAnalysis with band classification
        """
        # Prepare survey summary
        qa_text = "\n".join(
            [
                f"Q: {resp['question']}\nA: {resp['answer']}"
                for resp in survey_responses
            ]
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a sentiment analysis expert. Analyze survey responses to classify overall user sentiment.

Sentiment Bands:
- "good": User is satisfied, mostly positive feedback, likely to recommend
- "okay": Mixed feelings, some positives and negatives, neutral overall
- "bad": Dissatisfied, mostly negative feedback, significant concerns

Be accurate and consider:
- Explicit positive/negative statements
- Tone of responses
- Presence of critical issues vs minor concerns
- Overall satisfaction indicators""",
                ),
                (
                    "human",
                    """Product: {product_title}

Survey Responses:
{survey_qa}

Analyze the sentiment and classify into 'good', 'okay', or 'bad' band.

{format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.llm | self.sentiment_parser
        sentiment = chain.invoke(
            {
                "product_title": product_title,
                "survey_qa": qa_text,
                "format_instructions": self.sentiment_parser.get_format_instructions(),
            }
        )

        return sentiment

    def _analyze_writing_style(
        self, user_reviews: List[Dict[str, Any]]
    ) -> WritingStyleAnalysis:
        """
        Analyze user's writing style from previous reviews

        Args:
            user_reviews: List of user's previous reviews

        Returns:
            WritingStyleAnalysis with patterns and characteristics
        """
        # Prepare reviews text
        reviews_text = "\n\n---\n\n".join(
            [
                f"Review {idx + 1}:\n{review.get('review_text', review.get('text', ''))}"
                for idx, review in enumerate(user_reviews[:10])  # Limit to 10 reviews
            ]
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a writing style analysis expert. Analyze the user's previous reviews to identify their unique writing patterns.

Pay attention to:
- Average length and detail level
- Common phrases or expressions they use
- Tone (formal/casual, enthusiastic/measured, etc.)
- Vocabulary complexity
- Sentence structure patterns
- Unique stylistic elements

This analysis will be used to generate new reviews that match the user's natural writing style.""",
                ),
                (
                    "human",
                    """Analyze these previous reviews written by the user:

{reviews_text}

Total reviews analyzed: {review_count}

{format_instructions}""",
                ),
            ]
        )

        chain = prompt | self.llm
        response = chain.invoke(
            {
                "reviews_text": reviews_text,
                "review_count": len(user_reviews),
                "format_instructions": self.writing_style_parser.get_format_instructions(),
            }
        )

        # Parse the response manually to handle potential wrapper fields
        try:
            import json

            response_text = response.content if hasattr(response, "content") else str(response)

            # Strip markdown code block wrappers if present (```json\n...\n```)
            if response_text.startswith("```"):
                first_newline = response_text.find("\n")
                last_backticks = response_text.rfind("```")
                if first_newline != -1 and last_backticks != -1:
                    response_text = response_text[first_newline + 1:last_backticks].strip()

            json_obj = json.loads(response_text)

            # If the LLM wrapped the response with extra fields, extract the actual data
            # Common wrapper patterns: {"description": "...", ...actual_fields}
            if "description" in json_obj and len(json_obj) > 6:
                # Remove the description field and use the rest
                json_obj = {k: v for k, v in json_obj.items() if k != "description"}

            # Now validate with Pydantic
            writing_style = WritingStyleAnalysis(**json_obj)
            return writing_style

        except Exception as e:
            # If parsing fails, return a default writing style analysis
            print(f"Warning: Failed to parse writing style analysis: {e}")
            return WritingStyleAnalysis(
                has_previous_reviews=True,
                avg_review_length=sum(
                    len(r.get("review_text", r.get("text", "")).split())
                    for r in user_reviews
                )
                // len(user_reviews)
                if user_reviews
                else 0,
                writing_style_summary="User has previous reviews with varied writing patterns",
            )

    def _generate_review_options(
        self,
        sentiment: SentimentAnalysis,
        survey_responses: List[Dict[str, Any]],
        product_context: Dict[str, Any],
        customer_context: Dict[str, Any],
        product_title: str,
        writing_style: Optional[WritingStyleAnalysis] = None,
    ) -> ReviewOptions:
        """
        Generate 2-3 review options based on sentiment band

        Args:
            sentiment: Sentiment analysis result
            survey_responses: Original Q&A pairs
            product_context: Context from Agent 1
            customer_context: Context from Agent 2
            product_title: Product name

        Returns:
            ReviewOptions with appropriate star ratings
        """
        # Determine star ratings based on sentiment band
        star_ratings = self._get_star_ratings(sentiment.sentiment_band)

        # Prepare survey summary
        qa_text = "\n".join(
            [
                f"Q: {resp['question']}\nA: {resp['answer']}"
                for resp in survey_responses
            ]
        )

        # Create specialized prompt based on sentiment
        system_prompt = self._get_system_prompt(sentiment.sentiment_band)

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                (
                    "human",
                    """Product: {product_title}

Survey Responses:
{survey_qa}

Sentiment Analysis:
- Band: {sentiment_band}
- Positive Points: {positive_points}
- Negative Points: {negative_points}
- Overall: {overall_satisfaction}

Product Context:
{product_context}

Customer Context:
{customer_context}

{writing_style_section}

Generate {num_reviews} review options with star ratings: {star_ratings}

Each review should:
1. Be natural and authentic (like a real customer wrote it)
2. Reflect the survey responses accurately
3. Have appropriate length (50-150 words)
4. Match the assigned star rating in tone
5. Incorporate specific details from the survey
6. {writing_style_instruction}

{format_instructions}""",
                ),
            ]
        )

        # Prepare writing style section
        if writing_style and writing_style.has_previous_reviews:
            writing_style_section = f"""User's Writing Style Analysis:
- Average Review Length: {writing_style.avg_review_length} words
- Tone Characteristics: {', '.join(writing_style.tone_characteristics)}
- Vocabulary Level: {writing_style.vocabulary_level}
- Common Phrases: {', '.join(writing_style.common_phrases) if writing_style.common_phrases else 'None identified'}
- Style Summary: {writing_style.writing_style_summary}"""
            writing_style_instruction = "Match the user's unique writing style patterns identified above"
        else:
            writing_style_section = "User's Writing Style: No previous reviews available"
            writing_style_instruction = "Use natural, conversational language typical of online reviews"

        chain = prompt | self.llm | self.review_parser
        reviews = chain.invoke(
            {
                "product_title": product_title,
                "survey_qa": qa_text,
                "sentiment_band": sentiment.sentiment_band,
                "positive_points": ", ".join(sentiment.key_positive_points),
                "negative_points": ", ".join(sentiment.key_negative_points),
                "overall_satisfaction": sentiment.overall_satisfaction,
                "product_context": json.dumps(product_context, indent=2),
                "customer_context": json.dumps(customer_context, indent=2),
                "writing_style_section": writing_style_section,
                "writing_style_instruction": writing_style_instruction,
                "num_reviews": len(star_ratings),
                "star_ratings": ", ".join([f"{s} stars" for s in star_ratings]),
                "format_instructions": self.review_parser.get_format_instructions(),
            }
        )

        # Ensure star ratings match the expected values
        for i, review in enumerate(reviews.reviews):
            review.review_stars = star_ratings[i]

        reviews.sentiment_band = sentiment.sentiment_band

        return reviews

    def _get_star_ratings(self, sentiment_band: str) -> List[int]:
        """
        Map sentiment band to appropriate star ratings

        Args:
            sentiment_band: 'good', 'okay', or 'bad'

        Returns:
            List of star ratings (2-3 options)
        """
        if sentiment_band == "good":
            return [5, 4]  # 2 options: excellent and very good
        elif sentiment_band == "okay":
            return [4, 3, 2]  # 3 options: good, average, below average
        else:  # bad
            return [2, 1]  # 2 options: poor and very poor

    def _get_system_prompt(self, sentiment_band: str) -> str:
        """
        Get specialized system prompt based on sentiment

        Args:
            sentiment_band: 'good', 'okay', or 'bad'

        Returns:
            System prompt for review generation
        """
        base_prompt = """You are an expert review writer. Generate authentic, natural product reviews based on survey responses.

CRITICAL RULES:
1. Reviews must sound like real customers wrote them (not AI-generated)
2. Use conversational language and varied sentence structures
3. Include specific details from the survey responses
4. Match the tone to the star rating (5-star should be enthusiastic, 1-star critical)
5. Be honest and balanced - even positive reviews can mention minor drawbacks
6. Each review should have a slightly different focus/tone
"""

        if sentiment_band == "good":
            return (
                base_prompt
                + """
Sentiment: POSITIVE
Generate 2 reviews (5-star and 4-star):
- 5-star: Enthusiastic, highly recommend, focus on best features
- 4-star: Positive but balanced, mention minor areas for improvement
"""
            )
        elif sentiment_band == "okay":
            return (
                base_prompt
                + """
Sentiment: MIXED
Generate 3 reviews (4-star, 3-star, 2-star):
- 4-star: Emphasize positives, downplay negatives
- 3-star: Balanced, equal weight to pros and cons
- 2-star: Emphasize concerns, acknowledge some positives
"""
            )
        else:  # bad
            return (
                base_prompt
                + """
Sentiment: NEGATIVE
Generate 2 reviews (2-star and 1-star):
- 2-star: Critical but fair, mention some redeeming qualities
- 1-star: Strong disappointment, focus on major issues, minimal positives
"""
            )


# Global agent instance
review_gen_agent = ReviewGenAgent()
