"""
FastAPI Backend for Survey Sensei
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union
from config import settings
from agents import survey_agent
from agents.review_gen_agent import review_gen_agent
from agents.mock_data import MockDataOrchestrator, build_scenario_config
from integrations import RapidAPIClient
from database import db
import uvicorn
import time
from utils.logger import setup_logging, get_logger

# Setup enhanced logging
setup_logging(level="INFO", use_colors=True)
logger = get_logger(__name__)

app = FastAPI(
    title="Survey Sensei Backend",
    description="AI-powered survey generation and review creation backend",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests and responses with timing"""
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Only log non-health check endpoints
    if request.url.path not in ["/", "/health"]:
        # Log request and response in one line
        status_emoji = "✅" if response.status_code < 400 else "❌"
        logger.info(f"{status_emoji} {request.method} {request.url.path} → {response.status_code} ({duration_ms:.0f}ms)")

    return response


class GenerateMockDataRequest(BaseModel):
    """Request for generating mock data (FORM -> SUMMARY transition)"""
    user_id: str
    item_id: str
    form_data: Dict[str, Any]


class GenerateMockDataResponse(BaseModel):
    """Response with mock data metadata (for Summary pane)"""
    main_product_id: str
    main_user_id: str
    metadata: Dict[str, Any]  # Contains counts: products, users, transactions, reviews


class StartSurveyRequest(BaseModel):
    """Request for starting survey (SUMMARY -> SURVEY transition)"""
    user_id: str
    item_id: str
    form_data: Dict[str, Any]


class StartSurveyResponse(BaseModel):
    session_id: str
    question: Dict[str, Any]
    question_number: int
    total_questions: int
    answered_questions_count: int


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: Union[str, List[str]]


class EditAnswerRequest(BaseModel):
    session_id: str
    question_number: int
    answer: str


class GetQuestionForEditRequest(BaseModel):
    session_id: str
    question_number: int


class SubmitAnswerResponse(BaseModel):
    session_id: str
    status: str
    question: Optional[Dict[str, Any]] = None
    question_number: Optional[int] = None
    total_questions: Optional[int] = None
    answered_questions_count: Optional[int] = None
    skipped_count: Optional[int] = None
    consecutive_skips: Optional[int] = None


class SkipQuestionRequest(BaseModel):
    session_id: str


class GenerateReviewsRequest(BaseModel):
    session_id: str


class GenerateReviewsResponse(BaseModel):
    session_id: str
    status: str
    review_options: List[Dict[str, Any]]
    sentiment_band: str


class SubmitReviewRequest(BaseModel):
    session_id: str
    selected_review_index: int


class SubmitReviewResponse(BaseModel):
    session_id: str
    status: str
    review: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


class ProductPreviewRequest(BaseModel):
    asin: str


class ProductPreviewResponse(BaseModel):
    success: bool
    product: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/", response_model=HealthResponse)
async def root():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "environment": settings.environment,
    }


@app.post("/api/product/preview", response_model=ProductPreviewResponse)
async def preview_product(request: ProductPreviewRequest):
    """
    Preview product details from RapidAPI (for form UI display)
    This endpoint is called when user pastes Amazon URL to show product info

    Optimized flow:
    1. User pastes URL → Frontend extracts ASIN
    2. Frontend calls this endpoint → RapidAPI fetch (cached for 7 days)
    3. User fills form and submits → Backend reuses cached product data

    Total RapidAPI calls: 1 for product + 1 for reviews = 2 calls per submission
    """
    try:
        logger.info(f"📦 Product preview requested for ASIN: {request.asin}")
        rapidapi_client = RapidAPIClient()

        product = rapidapi_client.fetch_product_details(request.asin)

        if not product:
            return ProductPreviewResponse(
                success=False,
                error=f"Product not found or RapidAPI error for ASIN: {request.asin}"
            )

        logger.info(f"✅ Product preview successful: {product['title']}")
        return ProductPreviewResponse(
            success=True,
            product=product
        )

    except Exception as e:
        logger.error(f"Error in product preview: {str(e)}")
        return ProductPreviewResponse(
            success=False,
            error=str(e)
        )


@app.post("/api/mock-data/generate", response_model=GenerateMockDataResponse)
async def generate_mock_data(request: GenerateMockDataRequest):
    """
    Generate mock data ONLY (FORM -> SUMMARY transition)
    Does NOT start the survey - that happens on SUMMARY -> SURVEY transition

    Flow:
    1. Build scenario configuration from form data
    2. Fetch product details + reviews from RapidAPI
    3. Run MOCK_DATA_MINI_AGENT orchestrator to generate simulation data
    4. Insert all generated data into database
    5. Return metadata (counts, IDs) for Summary pane
    """
    try:
        logger.separator(f"Mock Data Generation: {request.item_id}")

        # STEP 1: Build scenario configuration
        scenario_config = build_scenario_config(request.form_data)
        logger.info(f"Scenario: {scenario_config['scenario_id']} ({scenario_config['group']})")

        # STEP 2: Fetch product details and reviews from RapidAPI
        rapidapi_client = RapidAPIClient()
        asin = request.item_id if request.item_id.startswith('B') else request.form_data.get('productASIN', request.item_id)

        main_product = rapidapi_client.fetch_product_details(asin)
        if not main_product:
            raise HTTPException(status_code=404, detail=f"Product not found: {asin}")

        # Fetch reviews only for warm products (Group A scenarios)
        api_reviews = []
        if scenario_config['group'] == 'warm_warm':
            api_reviews = rapidapi_client.fetch_product_reviews(asin, max_pages=2)
            logger.info(f"RapidAPI: {len(api_reviews)} reviews fetched")

        # STEP 3: Run MOCK_DATA orchestrator
        orchestrator = MockDataOrchestrator(use_cache=True)

        mock_data = await orchestrator.generate_simulation_data(
            form_data=request.form_data,
            main_product=main_product,
            api_reviews=api_reviews,
            scenario_config=scenario_config
        )
        logger.agent_complete(
            "Orchestrator",
            "data generation",
            products=mock_data['metadata']['product_count'],
            users=mock_data['metadata']['user_count'],
            transactions=mock_data['metadata']['transaction_count'],
            reviews=mock_data['metadata']['review_count']
        )

        # STEP 4: Clean up old mock data (for clean testing)
        try:
            deleted_counts = db.cleanup_mock_data()
            if sum(deleted_counts.values()) > 0:
                logger.info(f"Cleanup: {sum(deleted_counts.values())} rows deleted")
        except Exception as e:
            logger.warning(f"Cleanup warning: {str(e)}")

        # STEP 5: Insert new mock data into database

        # Deduplicate products by item_id (keep first occurrence, which is main product)
        seen_item_ids = set()
        unique_products = []
        for product in mock_data['products']:
            if product['item_id'] not in seen_item_ids:
                unique_products.append(product)
                seen_item_ids.add(product['item_id'])
            else:
                logger.warning(f"Skipping duplicate product: {product['item_id']}")

        # Deduplicate users by user_id
        seen_user_ids = set()
        unique_users = []
        for user in mock_data['users']:
            if user['user_id'] not in seen_user_ids:
                unique_users.append(user)
                seen_user_ids.add(user['user_id'])

        # Deduplicate transactions by transaction_id
        seen_transaction_ids = set()
        unique_transactions = []
        for transaction in mock_data['transactions']:
            if transaction['transaction_id'] not in seen_transaction_ids:
                unique_transactions.append(transaction)
                seen_transaction_ids.add(transaction['transaction_id'])

        # Deduplicate reviews by review_id
        seen_review_ids = set()
        unique_reviews = []
        for review in mock_data['reviews']:
            if review['review_id'] not in seen_review_ids:
                unique_reviews.append(review)
                seen_review_ids.add(review['review_id'])

        # Insert into database
        db.insert_products_batch(unique_products)
        db.insert_users_batch(unique_users)
        db.insert_transactions_batch(unique_transactions)
        db.insert_reviews_batch(unique_reviews)

        logger.info(f"Database: {len(unique_products)}p {len(unique_users)}u {len(unique_transactions)}t {len(unique_reviews)}r inserted")
        logger.separator()

        # Return metadata for Summary pane (DO NOT start survey yet)
        return GenerateMockDataResponse(
            main_product_id=mock_data['metadata']['main_product_id'],
            main_user_id=mock_data['metadata']['main_user_id'],
            metadata=mock_data['metadata']
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Mock data generation failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate mock data: {str(e)}")


@app.post("/api/survey/start", response_model=StartSurveyResponse)
async def start_survey(request: StartSurveyRequest):
    """
    Start survey session ONLY (SUMMARY -> SURVEY transition)
    Assumes mock data was already generated by /api/mock-data/generate

    Flow:
    1. Use main user and product IDs from request (passed from Summary pane)
    2. Start survey with generated context from database
    """
    try:
        logger.info(f"📝 Starting survey session for user: {request.user_id}, product: {request.item_id}")

        # Start survey with main user and main product (data already in database)
        result = survey_agent.start_survey(
            user_id=request.user_id,
            item_id=request.item_id,
            form_data=request.form_data,
        )

        logger.info("🎉 Survey started successfully")
        return StartSurveyResponse(
            session_id=result["session_id"],
            question=result["question"],
            question_number=result["question_number"],
            total_questions=result["total_questions"],
            answered_questions_count=result.get("answered_questions_count", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"ERROR in start_survey: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to start survey: {str(e)}")


@app.post("/api/survey/answer", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """Submit answer, get next question or completion status"""
    try:
        result = survey_agent.submit_answer(
            session_id=request.session_id,
            answer=request.answer,
        )

        if result.get("status") == "survey_completed":
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="survey_completed",
                answered_questions_count=result.get("answered_questions_count", 0),
            )
        else:
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="continue",
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
                answered_questions_count=result.get("answered_questions_count", 0),
            )

    except Exception as e:
        import traceback
        print(f"ERROR in submit_answer: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")


@app.post("/api/survey/skip", response_model=SubmitAnswerResponse)
async def skip_question(request: SkipQuestionRequest):
    """Skip question and move to next"""
    try:
        result = survey_agent.skip_question(session_id=request.session_id)

        if result.get("status") == "survey_completed":
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="survey_completed",
                answered_questions_count=result.get("answered_questions_count", 0),
            )
        else:
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="continue",
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
                answered_questions_count=result.get("answered_questions_count", 0),
                skipped_count=result.get("skipped_count"),
                consecutive_skips=result.get("consecutive_skips"),
            )

    except ValueError as e:
        # Skip limit errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(f"ERROR in skip_question: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to skip question: {str(e)}")


@app.post("/api/survey/get-for-edit")
async def get_question_for_edit(request: GetQuestionForEditRequest):
    """Get original question for editing (works for both answered and skipped questions)"""
    try:
        print(f"GET QUESTION FOR EDIT - Session: {request.session_id}, Question: {request.question_number}")
        result = survey_agent.get_question_for_edit(
            session_id=request.session_id,
            question_number=request.question_number,
        )
        print(f"GET QUESTION FOR EDIT - Success: {result.get('question', {}).get('question_text', 'N/A')}")

        return {
            "session_id": result["session_id"],
            "question": result["question"],
            "question_number": result["question_number"],
            "is_edit_mode": result["is_edit_mode"],
        }

    except Exception as e:
        import traceback
        print(f"ERROR in get_question_for_edit: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get question for edit: {str(e)}")


@app.post("/api/survey/edit", response_model=SubmitAnswerResponse)
async def edit_answer(request: EditAnswerRequest):
    """Edit previous answer and branch from that point"""
    try:
        result = survey_agent.edit_answer(
            session_id=request.session_id,
            question_number=request.question_number,
            new_answer=request.answer,
        )

        if result.get("status") == "completed":
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="completed",
                review_options=result.get("review_options"),
            )
        else:
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="continue",
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
            )

    except Exception as e:
        import traceback
        print(f"ERROR in edit_answer: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to edit answer: {str(e)}")


@app.post("/api/reviews/generate", response_model=GenerateReviewsResponse)
async def generate_reviews(request: GenerateReviewsRequest):
    """Generate review options using Agent 4"""
    try:
        session = db.get_survey_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        product = db.get_product_by_id(current_state.get("item_id"))
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        user_id = current_state.get("user_id")
        user_reviews = db.get_user_reviews(user_id, limit=10) if user_id else []

        review_options = review_gen_agent.generate_reviews(
            survey_responses=current_state.get("answers", []),
            product_context=current_state.get("product_context", {}),
            customer_context=current_state.get("customer_context", {}),
            product_title=product.get("title", "this product"),
            user_reviews=user_reviews,
        )

        # Store generated reviews in session for later submission
        db.update_survey_session(
            session_id=request.session_id,
            conversation_history=current_state.get("conversation_history", []),
            state="reviews_generated",
            metadata={
                **session_context,
                "current_state": {
                    **current_state,
                    "generated_reviews": [r.dict() for r in review_options.reviews],
                },
            },
        )

        return GenerateReviewsResponse(
            session_id=request.session_id,
            status="reviews_generated",
            review_options=[r.dict() for r in review_options.reviews],
            sentiment_band=review_options.sentiment_band,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in generate_reviews: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate reviews: {str(e)}")


@app.post("/api/reviews/regenerate", response_model=GenerateReviewsResponse)
async def regenerate_reviews(request: GenerateReviewsRequest):
    """
    Regenerate review options (Refresh button functionality)

    This endpoint re-invokes Agent 4 to generate a fresh set of review options
    with the same sentiment band but different variations.

    Args:
        request: Session ID

    Returns:
        New set of review options
    """
    try:
        # Reuse the same logic as generate_reviews
        # Agent 4 will naturally generate different variations each time
        return await generate_reviews(request)

    except Exception as e:
        import traceback
        print(f"ERROR in regenerate_reviews: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to regenerate reviews: {str(e)}")


@app.post("/api/survey/review", response_model=SubmitReviewResponse)
async def submit_review(request: SubmitReviewRequest):
    """
    Submit selected review and complete survey

    This endpoint:
    1. Saves the user's selected review to database
    2. Marks survey session as completed
    3. Returns confirmation

    Args:
        request: Session ID and selected review index (0-2)

    Returns:
        Confirmation with saved review details
    """
    try:
        # Get session data
        session = db.get_survey_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session_context = session.get("session_context", {})
        current_state = session_context.get("current_state", {})

        # Get selected review from generated options
        generated_reviews = current_state.get("generated_reviews", [])
        if not generated_reviews or request.selected_review_index >= len(generated_reviews):
            raise HTTPException(status_code=400, detail="Invalid review index")

        selected_review = generated_reviews[request.selected_review_index]

        # Save review to database
        review_id = db.save_generated_review(
            user_id=current_state.get("user_id"),
            item_id=current_state.get("item_id"),
            review_text=selected_review.get("review_text"),
            rating=selected_review.get("review_stars"),
            sentiment_label=selected_review.get("tone", "neutral"),
            metadata={
                "session_id": request.session_id,
                "tone": selected_review.get("tone", "neutral"),
                "generated_by": "agent_4_review_gen",
                "highlights": selected_review.get("highlights", []),
            },
        )

        # Mark session as completed
        db.update_survey_session(
            session_id=request.session_id,
            conversation_history=current_state.get("conversation_history", []),
            state="completed",
            metadata={
                **session_context,
                "review_id": review_id,
                "completed": True,
            },
        )

        return SubmitReviewResponse(
            session_id=request.session_id,
            status="review_saved",
            review=selected_review,
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in submit_review: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")


@app.get("/api/survey/session/{session_id}")
async def get_survey_session(session_id: str):
    """
    Get survey session details

    Args:
        session_id: Survey session ID

    Returns:
        Session state and conversation history
    """
    try:
        session = db.get_survey_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return session

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")


@app.get("/api/survey/questions/{session_id}")
async def get_session_questions(session_id: str):
    """
    Get all questions for a survey session

    Args:
        session_id: Survey session ID

    Returns:
        List of all questions asked in this session
    """
    try:
        questions = db.get_session_questions(session_id)
        return {"session_id": session_id, "questions": questions}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=settings.environment == "development",
    )
