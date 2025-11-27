"""
FastAPI Backend for Survey Sensei
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union
from config import settings
from agents import survey_agent
from agents.review_gen_agent import review_gen_agent
from database import db
import uvicorn

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


class StartSurveyRequest(BaseModel):
    user_id: str
    item_id: str
    form_data: Dict[str, Any]


class StartSurveyResponse(BaseModel):
    session_id: str
    question: Dict[str, Any]
    question_number: int
    total_questions: int


class SubmitAnswerRequest(BaseModel):
    session_id: str
    answer: Union[str, List[str]]


class EditAnswerRequest(BaseModel):
    session_id: str
    question_number: int
    answer: str


class SubmitAnswerResponse(BaseModel):
    session_id: str
    status: str
    question: Optional[Dict[str, Any]] = None
    question_number: Optional[int] = None
    total_questions: Optional[int] = None
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


@app.post("/api/survey/start", response_model=StartSurveyResponse)
async def start_survey(request: StartSurveyRequest):
    """Start new survey session, return first question"""
    try:
        result = survey_agent.start_survey(
            user_id=request.user_id,
            item_id=request.item_id,
            form_data=request.form_data,
        )

        return StartSurveyResponse(
            session_id=result["session_id"],
            question=result["question"],
            question_number=result["question_number"],
            total_questions=result["total_questions"],
        )

    except Exception as e:
        import traceback
        print(f"ERROR in start_survey: {str(e)}")
        print(traceback.format_exc())
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
            )
        else:
            return SubmitAnswerResponse(
                session_id=result["session_id"],
                status="continue",
                question=result["question"],
                question_number=result["question_number"],
                total_questions=result["total_questions"],
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
